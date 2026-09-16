"""Ночные задачи arq: полный пересчёт радара и подсказки норм по накопленной истории.

Контейнер живёт в UTC, поэтому 00:00 UTC — это 03:00 МСК, как записано в плане.
Запуск: `arq app.worker.WorkerSettings`.
"""

from datetime import UTC, datetime
from typing import Any, ClassVar

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import get_sessionmaker
from app.modules.interactions.models import Interaction
from app.modules.radar.service import recompute_signals
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


async def refresh_norm_suggestions(ctx: dict[str, Any]) -> int:
    """Обновляет подсказки норм: медиану и 80-й перцентиль завершённых этапов."""
    async with get_sessionmaker()() as session:
        updated = await refresh_suggestions(session)
        await session.commit()
        return updated


class WorkerSettings:
    functions: ClassVar[list[Any]] = [recompute_radar, refresh_norm_suggestions]
    cron_jobs: ClassVar[list[Any]] = [
        cron(recompute_radar, hour=RADAR_HOUR_UTC, minute=0),
        cron(refresh_norm_suggestions, hour=RADAR_HOUR_UTC, minute=SUGGESTIONS_MINUTE),
    ]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
