"""Задачи arq: пересчёт радара, эскалация зависших записей, подсказки норм, отчёты, синхронизация
и доставка уведомлений.

Контейнер живёт в UTC, поэтому 00:00 UTC — это 03:00 МСК, как записано в плане.
Запуск: `arq app.worker.WorkerSettings`.
"""

import uuid
from datetime import UTC, datetime
from typing import Any, ClassVar

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import get_sessionmaker
from app.core.security import current_user_for
from app.modules.catalogs.models import AppUser
from app.modules.integrations.outbox import push_all
from app.modules.integrations.service import ensure_sources, sync_all
from app.modules.interactions.models import Interaction
from app.modules.notifications.escalation import escalate_stalled
from app.modules.notifications.service import deliver_pending
from app.modules.radar.service import recompute_signals
from app.modules.reports.service import run_job
from app.modules.workflow.service import refresh_suggestions

RADAR_HOUR_UTC = 0
ESCALATION_MINUTE = 10
SUGGESTIONS_MINUTE = 20


async def recompute_radar(ctx: dict[str, Any]) -> int:
    """Пересчитывает сигналы всех активных взаимодействий: время идёт и без переходов."""
    async with get_sessionmaker()() as session:
        ids = list(
            await session.scalars(select(Interaction.id).where(Interaction.status == "active"))
        )
        await recompute_signals(session, ids, datetime.now(UTC))
        await session.commit()
        return len(ids)


async def build_report(ctx: dict[str, Any], job_id: str, user_id: str) -> str:
    """Строит заказанный отчёт. Область видимости берётся у заказчика, а не у воркера."""
    async with get_sessionmaker()() as session:
        requester = await session.get(AppUser, uuid.UUID(user_id))
        if requester is None:
            return "failed"
        # Вместе с правилами доступа: иначе отчёт из очереди показал бы больше, чем видит заказчик.
        user = await current_user_for(session, requester)
        job = await run_job(session, user, uuid.UUID(job_id))
        return job.status


async def sync_integrations(ctx: dict[str, Any]) -> int:
    """Часовая синхронизация LMS и сайта. Отказ одного источника не трогает остальные."""
    async with get_sessionmaker()() as session:
        await ensure_sources(session)
        runs = await sync_all(session, datetime.now(UTC))
        return sum(1 for run in runs if run.status == "done")


async def push_integrations(ctx: dict[str, Any]) -> int:
    """Отправляет изменения записей в LMS и CMS сайта. Отказ одного получателя не трогает других."""
    async with get_sessionmaker()() as session:
        runs = await push_all(session, datetime.now(UTC))
        return sum(int(run.stats.get("sent", 0)) for run in runs)


async def escalate_stalled_interactions(ctx: dict[str, Any]) -> int:
    """Уведомляет руководителей о записях без изменений дольше срока из настройки."""
    async with get_sessionmaker()() as session:
        return await escalate_stalled(session, datetime.now(UTC))


async def deliver_notifications(ctx: dict[str, Any]) -> int:
    """Отправляет созревшие уведомления в Telegram, Max и почту; отказ повторится позже."""
    async with get_sessionmaker()() as session:
        stats = await deliver_pending(session, datetime.now(UTC))
        return stats.sent


async def refresh_norm_suggestions(ctx: dict[str, Any]) -> int:
    """Обновляет подсказки норм: медиану и 80-й перцентиль завершённых этапов."""
    async with get_sessionmaker()() as session:
        updated = await refresh_suggestions(session)
        await session.commit()
        return updated


class WorkerSettings:
    functions: ClassVar[list[Any]] = [
        recompute_radar,
        escalate_stalled_interactions,
        refresh_norm_suggestions,
        build_report,
        sync_integrations,
        push_integrations,
        deliver_notifications,
    ]
    cron_jobs: ClassVar[list[Any]] = [
        cron(recompute_radar, hour=RADAR_HOUR_UTC, minute=0),
        cron(escalate_stalled_interactions, hour=RADAR_HOUR_UTC, minute=ESCALATION_MINUTE),
        cron(refresh_norm_suggestions, hour=RADAR_HOUR_UTC, minute=SUGGESTIONS_MINUTE),
        # Раз в минуту: уведомления не требуют мгновенности, но и не копятся часами.
        cron(deliver_notifications, second=30),
        # Раз в минуту: изменения записей уходят в LMS и CMS пакетом, онлайн жюри не требует.
        cron(push_integrations, second=45),
        # Раз в час: свежие метрики LMS и заявки сайта.
        cron(sync_integrations, minute=5),
    ]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
