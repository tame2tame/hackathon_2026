"""Статистика процесса: воронка по этапам, длительности этапов и распределение по направлениям.

Каждый график отдаётся вместе с настройками ECharts, поэтому интерфейс и PDF рисуют одно и то же.
"""

import uuid
from collections import defaultdict
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.errors import AppError, ErrorCode
from app.core.scope import apply_interaction_scope
from app.core.security import CurrentUser
from app.modules.analytics.schemas import ChartOut
from app.modules.catalogs.models import CounterpartyGroup, Direction, Program
from app.modules.interactions.models import Interaction, Transition
from app.modules.workflow.defaults import universities_group
from app.modules.workflow.models import Stage, WorkflowVersion
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


# Воронка показывает, где идёт работа: завершённые и отменённые записи в ней не стоят.
OPEN_STATUSES = ("active", "paused")


async def funnel(
    session: AsyncSession, user: CurrentUser, group_id: uuid.UUID | None = None
) -> ChartOut:
    """Сколько открытых взаимодействий стоит на каждом этапе — в порядке этапов процесса.

    Область видимости применяется к записям до соединения с этапами: иначе у всех, кроме
    администратора, из графика исчезали этапы, на которых у пользователя нет записей.
    """
    group, process = await _group(session, group_id)
    scoped = apply_interaction_scope(
        select(Interaction.id, Interaction.current_stage_id).where(
            Interaction.group_id == group.id, Interaction.status.in_(OPEN_STATUSES)
        ),
        user,
    ).subquery()
    stmt = (
        select(Stage.name, Stage.position, func.count(scoped.c.id))
        .select_from(Stage)
        .outerjoin(scoped, scoped.c.current_stage_id == Stage.id)
        .where(Stage.version_id == process.version.id)
        .group_by(Stage.name, Stage.position)
        .order_by(Stage.position)
    )
    rows = (await session.execute(stmt)).tuples().all()
    return _chart("Взаимодействия по этапам", [(name, count) for name, _, count in rows])


async def stage_durations(
    session: AsyncSession, user: CurrentUser, group_id: uuid.UUID | None = None
) -> ChartOut:
    """Средняя длительность завершённых этапов в днях: видно, где процесс вязнет.

    Этап узнаётся по коду во всех версиях процесса, а не только в действующей: иначе после
    любой публикации история пропадала бы целиком. Перенос записи на ту же схему
    (`source = migration` без смены этапа) границей этапа не считается — запись на нём
    просто продолжала стоять.
    """
    group, process = await _group(session, group_id)
    to_stage = aliased(Stage)
    from_stage = aliased(Stage)
    versions = select(WorkflowVersion.id).where(
        WorkflowVersion.template_id == process.version.template_id
    )
    boundaries = (
        apply_interaction_scope(
            select(
                Transition.interaction_id,
                Transition.occurred_at,
                to_stage.code.label("code"),
            )
            .select_from(Transition)
            .join(to_stage, to_stage.id == Transition.to_stage_id)
            .outerjoin(from_stage, from_stage.id == Transition.from_stage_id)
            .join(Interaction, Interaction.id == Transition.interaction_id)
            .where(
                to_stage.version_id.in_(versions),
                Interaction.group_id == group.id,
                or_(
                    Transition.source != "migration",
                    from_stage.code.is_(None),
                    from_stage.code != to_stage.code,
                ),
            ),
            user,
        )
    ).subquery()
    next_at = func.lead(boundaries.c.occurred_at).over(
        partition_by=boundaries.c.interaction_id, order_by=boundaries.c.occurred_at
    )
    stmt = select(boundaries.c.code, boundaries.c.occurred_at, next_at.label("next_at"))
    rows = (await session.execute(stmt)).tuples().all()

    durations: dict[str, list[int]] = defaultdict(list)
    for code, occurred_at, next_occurred in rows:
        if next_occurred is not None and code in process.stages:
            durations[code].append((next_occurred - occurred_at).days)
    ordered = sorted(durations.items(), key=lambda item: process.stages[item[0]].position)
    pairs = [
        (process.stages[code].name, round(sum(values) / len(values)))
        for code, values in ordered
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
