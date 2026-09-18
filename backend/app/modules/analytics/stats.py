"""Статистика процесса: воронка по этапам, длительности этапов и распределение по направлениям.

Каждый график отдаётся вместе с настройками ECharts, поэтому интерфейс и PDF рисуют одно и то же.
"""

import uuid
from collections import defaultdict
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ErrorCode
from app.core.scope import apply_interaction_scope
from app.core.security import CurrentUser
from app.modules.analytics.schemas import ChartOut
from app.modules.catalogs.models import CounterpartyGroup, Direction, Program
from app.modules.interactions.models import Interaction, Transition
from app.modules.workflow.defaults import universities_group
from app.modules.workflow.models import Stage
from app.modules.workflow.service import GroupProcess, group_process


def _bar_option(
    title: str, labels: list[str], values: list[int], color: str = "#2f6fed"
) -> dict[str, Any]:
    return {
        "title": {"text": title},
        "tooltip": {"trigger": "axis"},
        "grid": {"left": 8, "right": 8, "bottom": 8, "containLabel": True},
        "xAxis": {"type": "category", "data": labels, "axisLabel": {"interval": 0, "rotate": 30}},
        "yAxis": {"type": "value"},
        "series": [{"type": "bar", "data": values, "itemStyle": {"color": color}}],
    }


def _chart(title: str, pairs: list[tuple[str, int]], color: str = "#2f6fed") -> ChartOut:
    labels = [label for label, _ in pairs]
    values = [value for _, value in pairs]
    return ChartOut(
        title=title, labels=labels, values=values, option=_bar_option(title, labels, values, color)
    )


async def _group(
    session: AsyncSession, group_id: uuid.UUID | None
) -> tuple[CounterpartyGroup, GroupProcess]:
    """Группа графика; без неё — вузы, как было до появления групп."""
    group = (
        await session.get(CounterpartyGroup, group_id)
        if group_id is not None
        else await universities_group(session)
    )
    if group is None:
        raise AppError(ErrorCode.NOT_FOUND, "Группа контрагентов не найдена.")
    return group, await group_process(session, group)


async def funnel(
    session: AsyncSession, user: CurrentUser, group_id: uuid.UUID | None = None
) -> ChartOut:
    """Сколько активных взаимодействий стоит на каждом этапе — в порядке этапов процесса."""
    group, process = await _group(session, group_id)
    stmt = (
        select(Stage.name, Stage.position, func.count(Interaction.id))
        .select_from(Stage)
        .outerjoin(
            Interaction,
            and_(Interaction.current_stage_id == Stage.id, Interaction.group_id == group.id),
        )
        .where(Stage.version_id == process.version.id)
        .group_by(Stage.name, Stage.position)
        .order_by(Stage.position)
    )
    rows = (await session.execute(apply_interaction_scope(stmt, user))).tuples().all()
    return _chart("Взаимодействия по этапам", [(name, count) for name, _, count in rows])


async def stage_durations(
    session: AsyncSession, user: CurrentUser, group_id: uuid.UUID | None = None
) -> ChartOut:
    """Средняя длительность завершённых этапов в днях: видно, где процесс вязнет."""
    group, process = await _group(session, group_id)
    next_at = func.lead(Transition.occurred_at).over(
        partition_by=Transition.interaction_id, order_by=Transition.occurred_at
    )
    stmt = (
        select(Stage.name, Stage.position, Transition.occurred_at, next_at.label("next_at"))
        .select_from(Transition)
        .join(Stage, Stage.id == Transition.to_stage_id)
        .join(Interaction, Interaction.id == Transition.interaction_id)
        .where(Stage.version_id == process.version.id, Interaction.group_id == group.id)
    )
    rows = (await session.execute(apply_interaction_scope(stmt, user))).tuples().all()

    durations: dict[tuple[int, str], list[int]] = defaultdict(list)
    for name, position, occurred_at, next_occurred in rows:
        if next_occurred is not None:
            durations[(position, name)].append((next_occurred - occurred_at).days)
    pairs = [
        (name, round(sum(values) / len(values)))
        for (_, name), values in sorted(durations.items())
        if values
    ]
    return _chart("Средняя длительность этапа, дней", pairs, color="#e07b39")


async def distribution(
    session: AsyncSession, user: CurrentUser, group_id: uuid.UUID | None = None
) -> ChartOut:
    """Распределение взаимодействий по ИТ-направлениям; без группы — по всем группам."""
    stmt = (
        select(Direction.name, func.count(Interaction.id))
        .select_from(Interaction)
        .join(Program, Program.id == Interaction.program_id)
        .join(Direction, Direction.id == Program.direction_id)
        .where(Interaction.status != "cancelled")
        .group_by(Direction.name)
        .order_by(func.count(Interaction.id).desc())
    )
    if group_id is not None:
        stmt = stmt.where(Interaction.group_id == group_id)
    rows = (await session.execute(apply_interaction_scope(stmt, user))).tuples().all()
    return _chart("Взаимодействия по направлениям", list(rows), color="#3c9a5f")
