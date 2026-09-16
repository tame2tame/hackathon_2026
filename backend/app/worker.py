"""Ночные задачи arq: полный пересчёт радара и подсказки норм по накопленной истории.

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
from app.core.roles import Role
from app.core.security import CurrentUser
from app.modules.catalogs.models import AppUser
from app.modules.integrations.service import ensure_sources, sync_all
from app.modules.interactions.models import Interaction
from app.modules.radar.service import recompute_signals
from app.modules.reports.service import run_job
from app.modules.workflow.service import refresh_suggestions

RADAR_HOUR_UTC = 0
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
        user = CurrentUser(
            id=requester.id,
            email=requester.email,
            full_name=requester.full_name,
            role=Role(requester.role),
            team_id=requester.team_id,
        )
        job = await run_job(session, user, uuid.UUID(job_id))
        return job.status


async def sync_integrations(ctx: dict[str, Any]) -> int:
    """Часовая синхронизация LMS и сайта. Отказ одного источника не трогает остальные."""
    async with get_sessionmaker()() as session:
        await ensure_sources(session)
        runs = await sync_all(session, datetime.now(UTC))
        return sum(1 for run in runs if run.status == "done")


async def refresh_norm_suggestions(ctx: dict[str, Any]) -> int:
    """Обновляет подсказки норм: медиану и 80-й перцентиль завершённых этапов."""
    async with get_sessionmaker()() as session:
        updated = await refresh_suggestions(session)
        await session.commit()
        return updated


class WorkerSettings:
    functions: ClassVar[list[Any]] = [
        recompute_radar,
        refresh_norm_suggestions,
        build_report,
        sync_integrations,
    ]
    cron_jobs: ClassVar[list[Any]] = [
        cron(recompute_radar, hour=RADAR_HOUR_UTC, minute=0),
        cron(refresh_norm_suggestions, hour=RADAR_HOUR_UTC, minute=SUGGESTIONS_MINUTE),
        # Раз в час: свежие метрики LMS и заявки сайта.
        cron(sync_integrations, minute=5),
    ]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
