"""Строки отчёта: фильтры списка плюс этап, на котором взаимодействие было к концу периода."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.scope import apply_interaction_scope
from app.core.security import CurrentUser
from app.modules.catalogs.models import AppUser, Direction, Product, Program, University
from app.modules.interactions.models import Contract, Interaction, Transition
from app.modules.interactions.service import InteractionFilters, apply_filters
from app.modules.radar.models import RadarSignal
from app.modules.reports.schemas import COLUMNS
from app.modules.workflow.models import Stage

# Предел из плана: отчёт крупнее уже не читают, а строят по нему выгрузку в базу.
MAX_ROWS = 50_000


def headers(columns: list[str]) -> list[str]:
    return [COLUMNS[column] for column in columns]


def _period_end(filters: InteractionFilters, now: datetime) -> datetime:
    """Конец периода в UTC; без него отчёт описывает сегодняшний день."""
    if filters.period_to is None:
        return now
    return datetime.combine(filters.period_to, datetime.max.time(), tzinfo=UTC)


def _base_query(
    user: CurrentUser, filters: InteractionFilters, end: datetime
) -> Select[tuple[Any, ...]]:
    # Последний переход до конца периода: он и задаёт этап того времени (ADR-005).
    stage_at = (
        select(
            Transition.interaction_id,
            Transition.to_stage_id.label("stage_id"),
            Transition.occurred_at.label("entered_at"),
        )
        .where(Transition.occurred_at <= end)
        .distinct(Transition.interaction_id)
        .order_by(Transition.interaction_id, Transition.occurred_at.desc(), Transition.id.desc())
        .subquery()
    )
    open_signals = (
        select(
            RadarSignal.interaction_id,
            func.string_agg(RadarSignal.kind, ", ").label("kinds"),
        )
        .where(RadarSignal.resolved_at.is_(None))
        .group_by(RadarSignal.interaction_id)
        .subquery()
    )
    stmt = (
        select(
            University.name,
            Direction.name,
            Program.name,
            Product.name,
            Stage.name,
            AppUser.full_name,
            Contract.number,
            Contract.license_valid_until,
            stage_at.c.entered_at,
            Interaction.stage_entered_at,
            open_signals.c.kinds,
        )
        .select_from(Interaction)
        .join(University, University.id == Interaction.university_id)
        .join(Program, Program.id == Interaction.program_id)
        .join(Direction, Direction.id == Program.direction_id)
        .join(Product, Product.id == Interaction.product_id)
        .join(AppUser, AppUser.id == Interaction.owner_user_id)
        .outerjoin(Contract, Contract.id == Interaction.contract_id)
        .outerjoin(stage_at, stage_at.c.interaction_id == Interaction.id)
        .outerjoin(Stage, Stage.id == stage_at.c.stage_id)
        .outerjoin(open_signals, open_signals.c.interaction_id == Interaction.id)
    )
    return apply_filters(apply_interaction_scope(stmt, user), filters)


async def count_rows(
    session: AsyncSession,
    user: CurrentUser,
    filters: InteractionFilters,
    now: datetime | None = None,
) -> int:
    now = now or datetime.now(UTC)
    stmt = _base_query(user, filters, _period_end(filters, now))
    total: int = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    return total


async def build_rows(
    session: AsyncSession,
    user: CurrentUser,
    filters: InteractionFilters,
    columns: list[str],
    now: datetime | None = None,
) -> list[list[str]]:
    now = now or datetime.now(UTC)
    end = _period_end(filters, now)
    rows = await session.execute(
        _base_query(user, filters, end).order_by(University.name, Program.name, Product.name)
    )

    result: list[list[str]] = []
    for (
        university,
        direction,
        program,
        product,
        stage,
        owner,
        contract_number,
        license_valid_until,
        entered_at,
        stage_entered_at,
        signal_kinds,
    ) in rows.tuples():
        since = entered_at or stage_entered_at
        values = {
            "university": university,
            "direction": direction,
            "program": program,
            "product": product,
            "stage": stage or "",
            "owner": owner,
            "contract": contract_number or "",
            "license_valid_until": (
                license_valid_until.strftime("%d.%m.%Y") if license_valid_until else ""
            ),
            "days_on_stage": str(max(0, (end - since).days)),
            "signals": signal_kinds or "",
        }
        result.append([values[column] for column in columns])
    return result
