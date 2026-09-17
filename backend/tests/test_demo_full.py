"""Демо-стенд v1: детерминированность, идемпотентность и ровно заложенные проблемы."""

import random
from collections import Counter
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.demo_full import (
    B2C_KAM_TOTAL,
    B2C_OVERDUE_APPLICATION,
    B2C_TOTAL,
    HISTORY_MONTHS,
    INTERACTION_TOTAL,
    MISSING_DOCUMENT,
    OVERDUE_SIGNING,
    SEED,
    STALLED,
    UNIVERSITY_TOTAL,
    plans,
    seed_full,
    university_specs,
)
from app.modules.catalogs.models import AppUser, University
from app.modules.interactions.models import Interaction
from app.modules.metrics.models import METRIC_KINDS, ProgramMetric
from app.modules.radar.models import RadarSignal


async def open_signals(session: AsyncSession) -> Counter[str]:
    kinds = await session.scalars(select(RadarSignal.kind).where(RadarSignal.resolved_at.is_(None)))
    return Counter(kinds)


def test_generator_repeats_itself_with_the_same_seed() -> None:
    first = (university_specs(random.Random(SEED)), plans(random.Random(SEED), 50))  # noqa: S311
    second = (university_specs(random.Random(SEED)), plans(random.Random(SEED), 50))  # noqa: S311

    assert first == second


async def test_stand_is_loaded_once(session: AsyncSession) -> None:
    assert await seed_full(session, datetime.now(UTC)) is True

    universities = await session.scalar(select(func.count()).select_from(University))
    with_universities = await session.scalar(
        select(func.count()).select_from(Interaction).where(Interaction.university_id.is_not(None))
    )
    with_clients = await session.scalar(
        select(func.count()).select_from(Interaction).where(Interaction.client_id.is_not(None))
    )
    kams = await session.scalar(
        select(func.count()).select_from(AppUser).where(AppUser.role == "kam")
    )
    assert universities == UNIVERSITY_TOTAL
    # Двадцать КАМов вузов, двое из демо-данных v0 и команда частных клиентов.
    assert kams == 22 + B2C_KAM_TOTAL
    # Часть планов отсеивается совпадением тройки «вуз × программа × продукт».
    assert INTERACTION_TOTAL * 0.8 <= (with_universities or 0) <= INTERACTION_TOTAL + 6
    assert with_clients == B2C_TOTAL

    assert await seed_full(session, datetime.now(UTC)) is False


async def test_radar_finds_exactly_the_planted_problems(session: AsyncSession) -> None:
    before = await open_signals(session)

    await seed_full(session, datetime.now(UTC))

    added = await open_signals(session) - before
    assert added == Counter(
        {
            "stage_overdue": OVERDUE_SIGNING + B2C_OVERDUE_APPLICATION,
            "missing_document": MISSING_DOCUMENT,
            "inactivity": STALLED,
        }
    )


async def test_metrics_cover_a_year_by_three_kinds(session: AsyncSession) -> None:
    await seed_full(session, datetime.now(UTC))

    months = await session.scalar(select(func.count(func.distinct(ProgramMetric.period_month))))
    kinds = await session.scalars(select(func.distinct(ProgramMetric.metric)))
    smallest = await session.scalar(select(func.min(ProgramMetric.value)))

    assert months == HISTORY_MONTHS
    assert sorted(kinds) == sorted(METRIC_KINDS)
    assert smallest is not None
    assert smallest >= 1
