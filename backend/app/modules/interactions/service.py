"""Взаимодействия: список с фильтрами, карточка и переход между этапами."""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.interfaces import LoaderOption

from app.core.errors import AppError, ErrorCode, FieldError
from app.core.pagination import Page, PageParams
from app.core.scope import apply_interaction_scope
from app.core.security import CurrentUser
from app.modules.audit.models import AuditLog
from app.modules.catalogs.models import Product, Program, University
from app.modules.catalogs.schemas import ProductRef, ProgramRef, UniversityRef, UserRef
from app.modules.interactions.models import Attachment, Interaction, Transition
from app.modules.interactions.schemas import (
    ContractOut,
    InteractionDetail,
    InteractionListItem,
    SignalBrief,
    TransitionCreate,
    TransitionOut,
    TransitionResult,
)
from app.modules.radar.models import RadarSignal
from app.modules.radar.rules import Severity, SignalKind
from app.modules.radar.schemas import SignalOut
from app.modules.radar.service import like_pattern, open_signals_by_interaction, recompute_signals
from app.modules.workflow.models import Stage, StageNorm, WorkflowVersion
from app.modules.workflow.schemas import StageRef
from app.modules.workflow.service import allowed_transitions, get_transition_rule

NOT_FOUND_DETAIL = "Взаимодействие не найдено или недоступно."


@dataclass(slots=True)
class InteractionFilters:
    university_id: list[uuid.UUID] = field(default_factory=list)
    direction_id: list[uuid.UUID] = field(default_factory=list)
    program_id: list[uuid.UUID] = field(default_factory=list)
    product_id: list[uuid.UUID] = field(default_factory=list)
    owner_id: list[uuid.UUID] = field(default_factory=list)
    stage_code: list[str] = field(default_factory=list)
    has_signal: bool | None = None
    search: str | None = None


def _card_options() -> list[LoaderOption]:
    return [
        joinedload(Interaction.university),
        joinedload(Interaction.program).joinedload(Program.direction),
        joinedload(Interaction.product).joinedload(Product.vendor),
        joinedload(Interaction.owner),
        joinedload(Interaction.current_stage),
        joinedload(Interaction.contract),
        joinedload(Interaction.workflow_version),
    ]


def _apply_filters[S: Select[Any]](stmt: S, filters: InteractionFilters) -> S:
    stmt = stmt.where(Interaction.status != "cancelled")
    if filters.university_id:
        stmt = stmt.where(Interaction.university_id.in_(filters.university_id))
    if filters.program_id:
        stmt = stmt.where(Interaction.program_id.in_(filters.program_id))
    if filters.product_id:
        stmt = stmt.where(Interaction.product_id.in_(filters.product_id))
    if filters.owner_id:
        stmt = stmt.where(Interaction.owner_user_id.in_(filters.owner_id))
    if filters.direction_id:
        stmt = stmt.where(
            Interaction.program_id.in_(
                select(Program.id).where(Program.direction_id.in_(filters.direction_id))
            )
        )
    if filters.stage_code:
        stmt = stmt.where(
            Interaction.current_stage_id.in_(
                select(Stage.id).where(Stage.code.in_(filters.stage_code))
            )
        )
    if filters.has_signal is not None:
        has_open_signal = (
            select(RadarSignal.id)
            .where(RadarSignal.interaction_id == Interaction.id, RadarSignal.resolved_at.is_(None))
            .exists()
        )
        stmt = stmt.where(has_open_signal if filters.has_signal else ~has_open_signal)
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
    return stmt


async def _norms(session: AsyncSession, interactions: list[Interaction]) -> dict[uuid.UUID, int]:
    """Норма текущего этапа для каждого взаимодействия."""
    if not interactions:
        return {}
    rows = await session.execute(
        select(Interaction.id, StageNorm.norm_days)
        .join(Stage, Stage.id == Interaction.current_stage_id)
        .join(WorkflowVersion, WorkflowVersion.id == Interaction.workflow_version_id)
        .join(
            StageNorm,
            and_(
                StageNorm.template_id == WorkflowVersion.template_id,
                StageNorm.stage_code == Stage.code,
            ),
        )
        .where(Interaction.id.in_([i.id for i in interactions]))
    )
    return {interaction_id: days for interaction_id, days in rows.tuples()}


def _list_item(
    interaction: Interaction, signals: list[RadarSignal], norm_days: int | None, now: datetime
) -> InteractionListItem:
    return InteractionListItem(
        id=interaction.id,
        university=UniversityRef.model_validate(interaction.university),
        program=ProgramRef.model_validate(interaction.program),
        product=ProductRef.model_validate(interaction.product),
        owner=UserRef.model_validate(interaction.owner),
        stage=StageRef.model_validate(interaction.current_stage),
        stage_entered_at=interaction.stage_entered_at,
        days_on_stage=max(0, (now - interaction.stage_entered_at).days),
        norm_days=norm_days,
        status=interaction.status,
        version=interaction.version,
        last_activity_at=interaction.last_activity_at,
        open_signals=[
            SignalBrief(kind=SignalKind(s.kind), severity=Severity(s.severity)) for s in signals
        ],
    )


async def list_interactions(
    session: AsyncSession,
    user: CurrentUser,
    filters: InteractionFilters,
    page: PageParams,
    now: datetime | None = None,
) -> Page[InteractionListItem]:
    now = now or datetime.now(UTC)
    stmt = _apply_filters(apply_interaction_scope(select(Interaction), user), filters)
    total = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    interactions = list(
        (
            await session.scalars(
                stmt.options(*_card_options())
                .order_by(Interaction.stage_entered_at, Interaction.id)
                .offset(page.offset)
                .limit(page.page_size)
            )
        ).unique()
    )
    ids = [i.id for i in interactions]
    signals = await open_signals_by_interaction(session, ids)
    norms = await _norms(session, interactions)
    return Page(
        items=[_list_item(i, signals[i.id], norms.get(i.id), now) for i in interactions],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


async def get_interaction_detail(
    session: AsyncSession, user: CurrentUser, interaction_id: uuid.UUID, now: datetime | None = None
) -> InteractionDetail:
    now = now or datetime.now(UTC)
    stmt = apply_interaction_scope(
        select(Interaction).where(Interaction.id == interaction_id), user
    ).options(*_card_options())
    interaction = (await session.scalars(stmt)).unique().one_or_none()
    if interaction is None:
        raise AppError(ErrorCode.NOT_FOUND, NOT_FOUND_DETAIL)

    history = await session.scalars(
        select(Transition)
        .where(Transition.interaction_id == interaction_id)
        .options(
            joinedload(Transition.from_stage),
            joinedload(Transition.to_stage),
            joinedload(Transition.actor),
        )
        .order_by(Transition.occurred_at.desc(), Transition.id)
    )
    signals = (await open_signals_by_interaction(session, [interaction_id]))[interaction_id]
    norms = await _norms(session, [interaction])
    base = _list_item(interaction, signals, norms.get(interaction_id), now)
    return InteractionDetail(
        **base.model_dump(),
        workflow_version_id=interaction.workflow_version_id,
        contract=ContractOut.model_validate(interaction.contract) if interaction.contract else None,
        history=[_transition_out(t) for t in history],
        allowed_transitions=await allowed_transitions(session, interaction.current_stage_id),
        signals=[SignalOut.from_model(s) for s in signals],
    )


def _transition_out(transition: Transition) -> TransitionOut:
    return TransitionOut(
        id=transition.id,
        from_stage=StageRef.model_validate(transition.from_stage)
        if transition.from_stage
        else None,
        to_stage=StageRef.model_validate(transition.to_stage),
        occurred_at=transition.occurred_at,
        actor=UserRef.model_validate(transition.actor) if transition.actor else None,
        comment=transition.comment,
        source=transition.source,
    )


async def create_transition(
    session: AsyncSession,
    user: CurrentUser,
    interaction_id: uuid.UUID,
    payload: TransitionCreate,
    trace_id: str | None = None,
    now: datetime | None = None,
) -> TransitionResult:
    now = now or datetime.now(UTC)
    # Блокировка строки: два одновременных перехода не пройдут оба с одной версией.
    interaction = await session.scalar(
        apply_interaction_scope(
            select(Interaction).where(Interaction.id == interaction_id), user
        ).with_for_update()
    )
    if interaction is None:
        raise AppError(ErrorCode.NOT_FOUND, NOT_FOUND_DETAIL)
    if interaction.version != payload.expected_version:
        raise AppError(
            ErrorCode.INTERACTION_VERSION_CONFLICT,
            "Взаимодействие уже изменил другой пользователь. Обновите карточку и повторите.",
        )
    if interaction.status != "active":
        raise AppError(ErrorCode.WF_TRANSITION_NOT_ALLOWED, "Взаимодействие не активно.")

    rule = await get_transition_rule(session, interaction.current_stage_id, payload.to_stage_id)
    to_stage = await session.get(Stage, payload.to_stage_id)
    if rule is None or to_stage is None:
        raise AppError(
            ErrorCode.WF_TRANSITION_NOT_ALLOWED, "Переход в выбранный этап из текущего недоступен."
        )
    comment = payload.comment.strip()
    if rule.requires_comment and not comment:
        raise AppError(
            ErrorCode.WF_COMMENT_REQUIRED,
            f"Добавьте комментарий: без него переход на этап «{to_stage.name}» недоступен.",
            errors=[FieldError(field="comment", message="Обязательное поле")],
        )
    attachments = await _own_attachments(session, interaction_id, payload.attachment_ids)
    if rule.requires_attachment and not attachments:
        raise AppError(
            ErrorCode.WF_ATTACHMENT_REQUIRED,
            f"Приложите документ: без него переход на этап «{to_stage.name}» недоступен.",
            errors=[FieldError(field="attachment_ids", message="Нужен хотя бы один документ")],
        )

    before = {"stage_id": str(interaction.current_stage_id), "version": interaction.version}
    transition = Transition(
        interaction_id=interaction_id,
        from_stage_id=interaction.current_stage_id,
        to_stage_id=to_stage.id,
        occurred_at=now,
        actor_user_id=user.id,
        comment=comment or None,
        source="manual",
    )
    session.add(transition)
    await session.flush()
    for attachment in attachments:
        attachment.transition_id = transition.id

    interaction.current_stage_id = to_stage.id
    interaction.stage_entered_at = now
    interaction.last_activity_at = now
    interaction.version += 1
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="interaction.transition",
            entity_kind="interaction",
            entity_id=interaction_id,
            before=before,
            after={"stage_id": str(to_stage.id), "version": interaction.version},
            trace_id=trace_id,
        )
    )
    await session.flush()
    await recompute_signals(session, [interaction_id], now)
    await session.commit()

    detail = await get_interaction_detail(session, user, interaction_id, now)
    created = next(t for t in detail.history if t.id == transition.id)
    return TransitionResult(transition=created, interaction=detail)


async def _own_attachments(
    session: AsyncSession, interaction_id: uuid.UUID, attachment_ids: list[uuid.UUID]
) -> list[Attachment]:
    if not attachment_ids:
        return []
    attachments = list(
        await session.scalars(
            select(Attachment).where(
                Attachment.id.in_(attachment_ids), Attachment.interaction_id == interaction_id
            )
        )
    )
    if len(attachments) != len(set(attachment_ids)):
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Часть документов не найдена у этого взаимодействия.",
            errors=[FieldError(field="attachment_ids", message="Неизвестный документ")],
        )
    return attachments
