"""Рейтинг востребованности: метрики за период, веса и сравнение с предыдущим периодом."""

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ErrorCode, FieldError
from app.core.security import CurrentUser
from app.modules.analytics.models import RatingWeightSet
from app.modules.analytics.rating import DEFAULT_WEIGHTS, METRICS, Entry, RatingRow, rate
from app.modules.analytics.schemas import (
    ContributionOut,
    RatingEntity,
    RatingOrder,
    RatingOut,
    RatingRowOut,
    WeightsUpdate,
)
from app.modules.audit.models import AuditLog
from app.modules.catalogs.models import Direction, Program, University
from app.modules.metrics.models import ProgramMetric

DEFAULT_WEIGHTS_NAME = "По умолчанию"
DEFAULT_PERIOD_DAYS = 90
# Вузы сравниваются между собой целиком: у вуза нет направления, но группа нужна для нормирования.
ALL_UNIVERSITIES = uuid.UUID(int=0)
ALL_UNIVERSITIES_NAME = "Все вузы"


async def ensure_default_weights(session: AsyncSession) -> RatingWeightSet:
    """Набор весов по умолчанию: 40 заявки, 40 обучающиеся, 20 потоки."""
    weights = await session.scalar(
        select(RatingWeightSet).where(RatingWeightSet.is_default.is_(True))
    )
    if weights is None:
        weights = RatingWeightSet(
            name=DEFAULT_WEIGHTS_NAME,
            w_applications=DEFAULT_WEIGHTS["applications"],
            w_students=DEFAULT_WEIGHTS["students"],
            w_streams=DEFAULT_WEIGHTS["streams"],
            is_default=True,
        )
        session.add(weights)
        await session.flush()
    return weights


def weights_of(weights: RatingWeightSet) -> dict[str, int]:
    return {
        "applications": weights.w_applications,
        "students": weights.w_students,
        "streams": weights.w_streams,
    }


async def set_weights(
    session: AsyncSession, user: CurrentUser, payload: WeightsUpdate, trace_id: str | None = None
) -> RatingWeightSet:
    weights = await ensure_default_weights(session)
    before = weights_of(weights)
    weights.w_applications = payload.w_applications
    weights.w_students = payload.w_students
    weights.w_streams = payload.w_streams
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="rating.weights_changed",
            entity_kind="rating_weight_set",
            entity_id=weights.id,
            before=before,
            after=weights_of(weights),
            trace_id=trace_id,
        )
    )
    await session.commit()
    return weights


def _period(period_from: date | None, period_to: date | None) -> tuple[date, date]:
    end = period_to or datetime.now(UTC).date()
    start = period_from or end - timedelta(days=DEFAULT_PERIOD_DAYS)
    if start > end:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Начало периода позже его конца.",
            errors=[FieldError(field="period_from", message="Позже конца периода")],
        )
    return start, end


async def _entries(
    session: AsyncSession,
    entity: RatingEntity,
    start: date,
    end: date,
    direction_ids: list[uuid.UUID],
) -> list[Entry]:
    """Суммы метрик за период: по программам или по вузам."""
    stmt = (
        select(
            ProgramMetric.program_id,
            ProgramMetric.university_id,
            ProgramMetric.metric,
            func.sum(ProgramMetric.value),
        )
        .where(ProgramMetric.period_month >= start.replace(day=1))
        .where(ProgramMetric.period_month <= end)
        .group_by(ProgramMetric.program_id, ProgramMetric.university_id, ProgramMetric.metric)
    )
    rows = (await session.execute(stmt)).tuples().all()
    if not rows:
        return []

    programs = {
        program.id: program
        for program in await session.scalars(
            select(Program).where(Program.id.in_({row[0] for row in rows}))
        )
    }
    directions = {direction.id: direction for direction in await session.scalars(select(Direction))}
    universities = {
        university.id: university
        for university in await session.scalars(
            select(University).where(University.id.in_({row[1] for row in rows}))
        )
    }

    totals: dict[uuid.UUID, dict[str, float]] = {}
    labels: dict[uuid.UUID, tuple[str, uuid.UUID, str]] = {}
    for program_id, university_id, metric, value in rows:
        program = programs.get(program_id)
        if program is None or (direction_ids and program.direction_id not in direction_ids):
            continue
        if entity == "program":
            key = program_id
            direction = directions[program.direction_id]
            labels[key] = (program.name, direction.id, direction.name)
        else:
            university = universities.get(university_id)
            if university is None:
                continue
            key = university_id
            labels[key] = (university.short_name, ALL_UNIVERSITIES, ALL_UNIVERSITIES_NAME)
        totals.setdefault(key, {})[metric] = totals.setdefault(key, {}).get(metric, 0.0) + float(
            value
        )

    return [
        Entry(
            key=key,
            name=labels[key][0],
            direction_id=labels[key][1],
            direction_name=labels[key][2],
            values={metric: values[metric] for metric in METRICS if metric in values},
        )
        for key, values in totals.items()
    ]


async def rating(
    session: AsyncSession,
    entity: RatingEntity,
    period_from: date | None,
    period_to: date | None,
    direction_ids: list[uuid.UUID],
    weights: dict[str, int] | None = None,
    order: RatingOrder = "score",
) -> RatingOut:
    """Места за период и сдвиг относительно предыдущего периода такой же длины."""
    start, end = _period(period_from, period_to)
    if weights is None:
        weights = weights_of(await ensure_default_weights(session))

    current = rate(await _entries(session, entity, start, end, direction_ids), weights)
    span = max(1, (end - start).days)
    previous_end = start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=span)
    previous = rate(
        await _entries(session, entity, previous_start, previous_end, direction_ids), weights
    )
    places = {row.key: row.place for row in previous}
    priorities = {
        program_id: priority
        for program_id, priority in (
            await session.execute(select(Program.id, Program.priority))
        ).tuples()
    }

    rows = [_row_out(row, places.get(row.key), priorities.get(row.key, 0)) for row in current]
    if order == "priority":
        # Место остаётся местом по баллу: ручной приоритет меняет только порядок показа.
        rows.sort(key=lambda row: (-row.priority, row.place))
    return RatingOut(entity=entity, weights=weights, order=order, rows=rows)


def _row_out(row: RatingRow, previous_place: int | None, priority: int) -> RatingRowOut:
    return RatingRowOut(
        place=row.place,
        # Плюс — поднялись: было десятое место, стало третье, значит +7.
        place_change=None if previous_place is None else previous_place - row.place,
        id=row.key,
        name=row.name,
        direction_name=row.direction_name,
        score=row.score,
        priority=priority,
        contributions=[
            ContributionOut(
                metric=item.metric,
                weight=item.weight,
                value=item.value,
                normalized=item.normalized,
                contribution=item.contribution,
            )
            for item in row.contributions
        ],
        complete=row.complete,
        missing_metrics=row.missing_metrics,
    )
