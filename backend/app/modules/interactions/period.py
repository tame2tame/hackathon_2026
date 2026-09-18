"""Фильтр по периоду — одно правило для списков, сигналов и будущих отчётов.

Взаимодействие попадает в период, если создано не позже конца периода и либо всё ещё активно,
либо в периоде был хотя бы один переход. Даты сравниваются в UTC (ARCHITECTURE.md, раздел 5).
"""

from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import ColumnElement, and_, or_, select

from app.modules.interactions.models import Interaction, Transition


def _start_of_day(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=UTC)


def _after_day(day: date) -> datetime:
    return datetime.combine(day + timedelta(days=1), time.min, tzinfo=UTC)


def period_condition(
    period_from: date | None, period_to: date | None
) -> ColumnElement[bool] | None:
    if period_from is None and period_to is None:
        return None

    transitions = select(Transition.id).where(Transition.interaction_id == Interaction.id)
    if period_from is not None:
        transitions = transitions.where(Transition.occurred_at >= _start_of_day(period_from))
    if period_to is not None:
        transitions = transitions.where(Transition.occurred_at < _after_day(period_to))

    conditions: list[ColumnElement[bool]] = [
        or_(Interaction.status == "active", transitions.exists())
    ]
    if period_to is not None:
        conditions.append(Interaction.created_at < _after_day(period_to))
    return and_(*conditions)
