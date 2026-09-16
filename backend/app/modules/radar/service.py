"""Радар: загрузка состояния взаимодействий, пересчёт и выдача открытых сигналов."""

import uuid
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from sqlalchemy import ColumnElement, and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.pagination import Page, PageParams
from app.core.scope import apply_interaction_scope
from app.core.security import CurrentUser
from app.modules.catalogs.models import Product, Program, University
from app.modules.interactions.models import Attachment, Contract, Interaction
from app.modules.interactions.period import period_condition
from app.modules.radar.models import RadarSignal
from app.modules.radar.rules import (
    DEFAULT_THRESHOLDS,
    InteractionState,
    RadarThresholds,
    evaluate_signals,
)
from app.modules.radar.schemas import InteractionRef, SignalListItem, SignalOut
from app.modules.workflow.models import Stage, StageNorm, WorkflowVersion


@dataclass(slots=True)
class SignalFilters:
    kind: list[str] = field(default_factory=list)
    severity: list[str] = field(default_factory=list)
    owner_id: list[uuid.UUID] = field(default_factory=list)
    university_id: list[uuid.UUID] = field(default_factory=list)
    period_from: date | None = None
    period_to: date | None = None
    search: str | None = None


def like_pattern(text: str) -> str:
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


async def load_states(
    session: AsyncSession, interaction_ids: Sequence[uuid.UUID]
) -> dict[uuid.UUID, InteractionState]:
    rows = await session.execute(
        select(Interaction, Stage, Contract, StageNorm.norm_days, StageNorm.source)
        .join(Stage, Stage.id == Interaction.current_stage_id)
        .join(WorkflowVersion, WorkflowVersion.id == Interaction.workflow_version_id)
        .outerjoin(Contract, Contract.id == Interaction.contract_id)
        .outerjoin(
            StageNorm,
            and_(
                StageNorm.template_id == WorkflowVersion.template_id,
                StageNorm.stage_code == Stage.code,
            ),
        )
        .where(Interaction.id.in_(interaction_ids))
    )
    uploaded: dict[uuid.UUID, set[str]] = defaultdict(set)
    documents = await session.execute(
        select(Attachment.interaction_id, Attachment.document_type)
        .join(Interaction, Interaction.id == Attachment.interaction_id)
        .where(
            Attachment.interaction_id.in_(interaction_ids),
            Attachment.stage_id == Interaction.current_stage_id,
            Attachment.document_type.is_not(None),
        )
    )
    for interaction_id, document_type in documents.tuples():
        if document_type is not None:
            uploaded[interaction_id].add(document_type)

    states: dict[uuid.UUID, InteractionState] = {}
    for interaction, stage, contract, norm_days, norm_source in rows.tuples():
        states[interaction.id] = InteractionState(
            status=interaction.status,
            stage_code=stage.code,
            stage_name=stage.name,
            stage_kind=stage.kind,
            stage_entered_at=interaction.stage_entered_at,
            last_activity_at=interaction.last_activity_at,
            norm_days=norm_days,
            norm_source=norm_source,
            required_document_types=tuple(stage.required_document_types),
            uploaded_document_types=frozenset(uploaded[interaction.id]),
            contract_number=contract.number if contract else None,
            license_valid_until=contract.license_valid_until if contract else None,
        )
    return states


async def recompute_signals(
    session: AsyncSession,
    interaction_ids: Sequence[uuid.UUID],
    now: datetime | None = None,
    thresholds: RadarThresholds = DEFAULT_THRESHOLDS,
) -> None:
    """Открывает, обновляет и закрывает сигналы так, чтобы они соответствовали правилам на `now`."""
    now = now or datetime.now(UTC)
    states = await load_states(session, interaction_ids)
    open_signals = await session.scalars(
        select(RadarSignal).where(
            RadarSignal.interaction_id.in_(interaction_ids), RadarSignal.resolved_at.is_(None)
        )
    )
    current = {(signal.interaction_id, signal.kind): signal for signal in open_signals}

    for interaction_id, state in states.items():
        drafts = {draft.kind.value: draft for draft in evaluate_signals(state, now, thresholds)}
        for kind, draft in drafts.items():
            signal = current.pop((interaction_id, kind), None)
            if signal is None:
                session.add(
                    RadarSignal(
                        interaction_id=interaction_id,
                        kind=kind,
                        severity=draft.severity.value,
                        evidence=draft.evidence,
                        detected_at=now,
                    )
                )
            else:
                signal.severity = draft.severity.value
                signal.evidence = draft.evidence

    # Всё, что осталось открытым без подтверждения правилом, закрывается.
    for signal in current.values():
        signal.resolved_at = now
    await session.flush()


async def open_signals_by_interaction(
    session: AsyncSession, interaction_ids: Sequence[uuid.UUID]
) -> dict[uuid.UUID, list[RadarSignal]]:
    result: dict[uuid.UUID, list[RadarSignal]] = defaultdict(list)
    if not interaction_ids:
        return result
    signals = await session.scalars(
        select(RadarSignal)
        .where(RadarSignal.interaction_id.in_(interaction_ids), RadarSignal.resolved_at.is_(None))
        .order_by(_severity_rank(), RadarSignal.detected_at.desc())
    )
    for signal in signals:
        result[signal.interaction_id].append(signal)
    return result


def _severity_rank() -> ColumnElement[int]:
    return case({"high": 0, "medium": 1, "low": 2}, value=RadarSignal.severity)


async def list_signals(
    session: AsyncSession, user: CurrentUser, filters: SignalFilters, page: PageParams
) -> Page[SignalListItem]:
    stmt = (
        select(RadarSignal, Interaction)
        .join(Interaction, Interaction.id == RadarSignal.interaction_id)
        .where(RadarSignal.resolved_at.is_(None), Interaction.status != "cancelled")
    )
    stmt = apply_interaction_scope(stmt, user)
    if filters.kind:
        stmt = stmt.where(RadarSignal.kind.in_(filters.kind))
    if filters.severity:
        stmt = stmt.where(RadarSignal.severity.in_(filters.severity))
    if filters.owner_id:
        stmt = stmt.where(Interaction.owner_user_id.in_(filters.owner_id))
    if filters.university_id:
        stmt = stmt.where(Interaction.university_id.in_(filters.university_id))
    period = period_condition(filters.period_from, filters.period_to)
    if period is not None:
        stmt = stmt.where(period)
    if filters.search:
        pattern = like_pattern(filters.search)
        stmt = stmt.where(
            or_(
                Interaction.university_id.in_(
                    select(University.id).where(
                        or_(
                            University.name.ilike(pattern, escape="\\"),
                            University.short_name.ilike(pattern, escape="\\"),
                        )
                    )
                ),
                Interaction.program_id.in_(
                    select(Program.id).where(Program.name.ilike(pattern, escape="\\"))
                ),
                Interaction.product_id.in_(
                    select(Product.id).where(Product.name.ilike(pattern, escape="\\"))
                ),
            )
        )

    total = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = await session.execute(
        stmt.options(
            joinedload(Interaction.university),
            joinedload(Interaction.program).joinedload(Program.direction),
            joinedload(Interaction.product).joinedload(Product.vendor),
            joinedload(Interaction.owner),
        )
        .order_by(_severity_rank(), RadarSignal.detected_at.desc(), RadarSignal.id)
        .offset(page.offset)
        .limit(page.page_size)
    )
    items = [
        SignalListItem(
            **SignalOut.from_model(signal).model_dump(),
            interaction=InteractionRef.model_validate(interaction),
        )
        for signal, interaction in rows.unique().tuples()
    ]
    return Page(items=items, total=total, page=page.page, page_size=page.page_size)
