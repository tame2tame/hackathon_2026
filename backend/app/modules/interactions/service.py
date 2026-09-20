"""Взаимодействия: список с фильтрами, карточка и переход между этапами."""

import uuid
from collections import Counter
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.interfaces import LoaderOption

from app.core.errors import AppError, ErrorCode, FieldError
from app.core.events import (
    INTERACTION_CREATED,
    INTERACTION_STATUS_CHANGED,
    INTERACTION_TRANSITIONED,
    get_event_bus,
)
from app.core.pagination import Page, PageParams
from app.core.roles import Role
from app.core.scope import apply_interaction_scope, visible_interaction
from app.core.security import CurrentUser, current_user_for
from app.modules.audit.models import AuditLog
from app.modules.catalogs.models import (
    AppUser,
    CounterpartyGroup,
    Product,
    Program,
    ProgramProduct,
    University,
)
from app.modules.catalogs.schemas import (
    CounterpartyRef,
    GroupRef,
    ProductRef,
    ProgramRef,
    UniversityRef,
    UserRef,
)
from app.modules.clients.models import Client
from app.modules.clients.schemas import ClientRef
from app.modules.clients.service import visible_client
from app.modules.integrations.outbox import mark_changed
from app.modules.interactions.models import (
    AssignmentChange,
    Attachment,
    Interaction,
    InteractionNote,
    Transition,
)
from app.modules.interactions.period import period_condition
from app.modules.interactions.schemas import (
    BulkItemResult,
    BulkOwnerRequest,
    BulkResult,
    BulkTransitionRequest,
    ContractOut,
    InteractionCreate,
    InteractionDetail,
    InteractionListItem,
    NoteOut,
    OwnerChange,
    SignalBrief,
    StatusChange,
    TransitionCreate,
    TransitionOut,
    TransitionResult,
)
from app.modules.notifications.service import interaction_label, notify
from app.modules.radar.models import RadarSignal
from app.modules.radar.rules import Severity, SignalKind
from app.modules.radar.schemas import SignalOut
from app.modules.radar.service import like_pattern, open_signals_by_interaction, recompute_signals
from app.modules.workflow.models import Stage, StageNorm, WorkflowVersion
from app.modules.workflow.schemas import StageRef
from app.modules.workflow.service import allowed_transitions, get_transition_rule, group_process

NOT_FOUND_DETAIL = "Взаимодействие не найдено или недоступно."
STATUS_NAMES = {
    "active": "в работе",
    "paused": "приостановлена",
    "completed": "завершена",
    "cancelled": "отменена",
}


@dataclass(slots=True)
class InteractionFilters:
    group_id: list[uuid.UUID] = field(default_factory=list)
    client_id: list[uuid.UUID] = field(default_factory=list)
    university_id: list[uuid.UUID] = field(default_factory=list)
    direction_id: list[uuid.UUID] = field(default_factory=list)
    program_id: list[uuid.UUID] = field(default_factory=list)
    product_id: list[uuid.UUID] = field(default_factory=list)
    owner_id: list[uuid.UUID] = field(default_factory=list)
    stage_code: list[str] = field(default_factory=list)
    status: list[str] = field(default_factory=list)
    has_signal: bool | None = None
    period_from: date | None = None
    period_to: date | None = None
    search: str | None = None


def _card_options() -> list[LoaderOption]:
    return [
        joinedload(Interaction.group),
        joinedload(Interaction.university),
        joinedload(Interaction.client),
        joinedload(Interaction.program).joinedload(Program.direction),
        joinedload(Interaction.product).joinedload(Product.vendor),
        joinedload(Interaction.owner),
        joinedload(Interaction.current_stage),
        joinedload(Interaction.contract),
        joinedload(Interaction.workflow_version),
    ]


def apply_filters[S: Select[Any]](stmt: S, filters: InteractionFilters) -> S:
    """Фильтры списка. Отчёты берут те же самые, поэтому функция открыта наружу."""
    # Без явного фильтра отменённые записи не показываются: они закрыты решением человека.
    stmt = stmt.where(
        Interaction.status.in_(filters.status)
        if filters.status
        else Interaction.status != "cancelled"
    )
    period = period_condition(filters.period_from, filters.period_to)
    if period is not None:
        stmt = stmt.where(period)
    if filters.group_id:
        stmt = stmt.where(Interaction.group_id.in_(filters.group_id))
    if filters.client_id:
        stmt = stmt.where(Interaction.client_id.in_(filters.client_id))
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
                Interaction.client_id.in_(
                    select(Client.id).where(Client.name.ilike(pattern, escape="\\"))
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
        group=GroupRef.model_validate(interaction.group),
        counterparty=CounterpartyRef.model_validate(interaction.counterparty),
        university=UniversityRef.model_validate(interaction.university)
        if interaction.university
        else None,
        client=ClientRef.model_validate(interaction.client) if interaction.client else None,
        program=ProgramRef.model_validate(interaction.program),
        product=ProductRef.model_validate(interaction.product) if interaction.product else None,
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
    stmt = apply_filters(apply_interaction_scope(select(Interaction), user), filters)
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


async def _group(session: AsyncSession, group_id: uuid.UUID) -> CounterpartyGroup:
    group = await session.get(CounterpartyGroup, group_id)
    if group is None or group.archived_at is not None:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Группа контрагентов не найдена или в архиве.",
            errors=[FieldError(field="group_id", message="Неизвестная группа")],
        )
    return group


async def _counterparty(
    session: AsyncSession, user: CurrentUser, payload: InteractionCreate
) -> tuple[uuid.UUID | None, uuid.UUID | None]:
    if payload.university_id is not None and payload.client_id is None:
        university = await session.get(University, payload.university_id)
        if university is None or university.archived_at is not None:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Вуз не найден или в архиве.",
                errors=[FieldError(field="university_id", message="Неизвестный вуз")],
            )
        return university.id, None
    if payload.client_id is not None and payload.university_id is None:
        client = await visible_client(session, user, payload.client_id)
        if client.archived_at is not None:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Клиент в архиве.",
                errors=[FieldError(field="client_id", message="Клиент в архиве")],
            )
        return None, client.id
    raise AppError(
        ErrorCode.VALIDATION_ERROR,
        "Укажите контрагента: вуз или клиента, но не обоих сразу.",
        errors=[FieldError(field="university_id", message="Нужен ровно один контрагент")],
    )


async def _program_and_product(
    session: AsyncSession, program_id: uuid.UUID, product_id: uuid.UUID | None
) -> Program:
    """Продуктозависимой программе нужен её продукт; у продуктонезависимой его может не быть."""
    program = await session.get(Program, program_id)
    if program is None or program.archived_at is not None:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Программа не найдена или в архиве.",
            errors=[FieldError(field="program_id", message="Неизвестная программа")],
        )
    linked = set(
        await session.scalars(
            select(ProgramProduct.product_id).where(ProgramProduct.program_id == program.id)
        )
    )
    if product_id is None:
        if linked:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                f"Программа «{program.name}» идёт с продуктом: выберите его.",
                errors=[FieldError(field="product_id", message="Нужен продукт программы")],
            )
        return program
    product = await session.get(Product, product_id)
    if product is None or product.archived_at is not None:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Продукт не найден или в архиве.",
            errors=[FieldError(field="product_id", message="Неизвестный продукт")],
        )
    if linked and product.id not in linked:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            f"Продукт «{product.name}» не входит в программу «{program.name}».",
            errors=[FieldError(field="product_id", message="Продукт не из этой программы")],
        )
    return program


async def create_interaction(
    session: AsyncSession,
    user: CurrentUser,
    payload: InteractionCreate,
    trace_id: str | None = None,
    now: datetime | None = None,
) -> InteractionDetail:
    """Новая запись на первом этапе процесса своей группы."""
    now = now or datetime.now(UTC)
    group = await _group(session, payload.group_id)
    process = await group_process(session, group)
    version, start = process.version, process.start
    university_id, client_id = await _counterparty(session, user, payload)
    program = await _program_and_product(session, payload.program_id, payload.product_id)
    owner_id = payload.owner_id or user.id
    if owner_id != user.id:
        _ensure_can_assign(user)
        await _assignable_user(session, user, owner_id)

    same_counterparty = (
        Interaction.university_id == university_id
        if university_id is not None
        else Interaction.client_id == client_id
    )
    duplicate = await session.scalar(
        select(Interaction.id).where(
            same_counterparty,
            Interaction.program_id == program.id,
            Interaction.product_id.is_not_distinct_from(payload.product_id),
            Interaction.status != "cancelled",
        )
    )
    if duplicate is not None:
        raise AppError(
            ErrorCode.INTERACTION_DUPLICATE,
            "С этим контрагентом по этой программе и продукту запись уже ведётся.",
        )

    interaction = Interaction(
        group_id=group.id,
        university_id=university_id,
        client_id=client_id,
        program_id=program.id,
        product_id=payload.product_id,
        workflow_version_id=version.id,
        current_stage_id=start.id,
        stage_entered_at=now,
        owner_user_id=owner_id,
        source="manual",
        last_activity_at=now,
    )
    try:
        async with session.begin_nested():
            session.add(interaction)
            await session.flush()
    except IntegrityError as error:
        # Запись успели завести параллельно: уникальный индекс не пустил второй экземпляр.
        raise AppError(
            ErrorCode.INTERACTION_DUPLICATE,
            "С этим контрагентом по этой программе и продукту запись уже ведётся.",
        ) from error

    visible = await session.scalar(
        apply_interaction_scope(
            select(Interaction.id).where(Interaction.id == interaction.id), user
        )
    )
    if visible is None:
        raise AppError(
            ErrorCode.AUTH_FORBIDDEN,
            "Правила доступа не позволяют вести записи с этим контрагентом или в этой группе.",
        )
    comment = payload.comment.strip()
    session.add(
        Transition(
            interaction_id=interaction.id,
            from_stage_id=None,
            to_stage_id=start.id,
            occurred_at=now,
            actor_user_id=user.id,
            comment=comment or "Взаимодействие создано",
            source="manual",
        )
    )
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="interaction.created",
            entity_kind="interaction",
            entity_id=interaction.id,
            after={
                "group": group.code,
                "university_id": str(university_id) if university_id else None,
                "client_id": str(client_id) if client_id else None,
                "program_id": str(program.id),
                "product_id": str(payload.product_id) if payload.product_id else None,
                "owner_user_id": str(owner_id),
            },
            trace_id=trace_id,
        )
    )
    await session.flush()
    await recompute_signals(session, [interaction.id], now)
    await mark_changed(session, [interaction.id], "created")
    await session.commit()
    await get_event_bus().publish(
        INTERACTION_CREATED,
        {
            "interaction_id": str(interaction.id),
            "group_code": group.code,
            "stage_code": start.code,
        },
        owner_user_id=owner_id,
    )
    return await get_interaction_detail(session, user, interaction.id, now)


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

    transition = await _apply_transition(
        session,
        user,
        interaction,
        to_stage,
        comment,
        source="manual",
        attachments=attachments,
        trace_id=trace_id,
        now=now,
    )
    await recompute_signals(session, [interaction_id], now)
    await session.commit()

    detail = await get_interaction_detail(session, user, interaction_id, now)
    created = next(t for t in detail.history if t.id == transition.id)
    return TransitionResult(transition=created, interaction=detail)


async def _apply_transition(
    session: AsyncSession,
    user: CurrentUser,
    interaction: Interaction,
    to_stage: Stage,
    comment: str,
    *,
    source: str,
    attachments: list[Attachment],
    trace_id: str | None,
    now: datetime,
    notify_owner: bool = True,
) -> Transition:
    """Общая часть одиночного и группового перехода: история, карточка, аудит."""
    before = {"stage_id": str(interaction.current_stage_id), "version": interaction.version}
    transition = Transition(
        interaction_id=interaction.id,
        from_stage_id=interaction.current_stage_id,
        to_stage_id=to_stage.id,
        occurred_at=now,
        actor_user_id=user.id,
        comment=comment or None,
        source=source,
    )
    session.add(transition)
    await session.flush()
    for attachment in attachments:
        attachment.transition_id = transition.id

    from_stage_id = interaction.current_stage_id
    interaction.current_stage_id = to_stage.id
    interaction.stage_entered_at = now
    interaction.last_activity_at = now
    interaction.version += 1
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="interaction.transition",
            entity_kind="interaction",
            entity_id=interaction.id,
            before=before,
            after={"stage_id": str(to_stage.id), "version": interaction.version},
            trace_id=trace_id,
        )
    )
    await session.flush()
    await get_event_bus().publish(
        INTERACTION_TRANSITIONED,
        {
            "interaction_id": str(interaction.id),
            "to_stage_code": to_stage.code,
            "version": interaction.version,
            "source": source,
        },
        owner_user_id=interaction.owner_user_id,
    )
    if notify_owner and user.id != interaction.owner_user_id:
        await _notify_owner(session, user, interaction, from_stage_id, to_stage, comment)
    await mark_changed(session, [interaction.id], "transition")
    return transition


async def _notify_owner(
    session: AsyncSession,
    user: CurrentUser,
    interaction: Interaction,
    from_stage_id: uuid.UUID,
    to_stage: Stage,
    comment: str,
) -> None:
    """Запись перевёл не владелец: руководитель, групповой переход — владелец должен узнать."""
    owner = await session.get(AppUser, interaction.owner_user_id)
    if owner is None or not owner.is_active:
        return
    # Правило доступа могло закрыть запись самому владельцу: тогда и уведомлять его нечем.
    visible = await session.scalar(
        apply_interaction_scope(
            select(Interaction.id).where(Interaction.id == interaction.id),
            await current_user_for(session, owner),
        )
    )
    if visible is None:
        return
    from_stage = await session.get(Stage, from_stage_id)
    label = await interaction_label(session, interaction.id)
    body = (
        f"{user.full_name} перевёл(а) «{label}» с этапа «{from_stage.name if from_stage else '—'}» "
        f"на «{to_stage.name}»."
    )
    if comment:
        body += f" Комментарий: {comment}"
    await notify(
        session,
        [interaction.owner_user_id],
        "stage_changed",
        f"Запись переведена на этап «{to_stage.name}»",
        body,
        interaction_id=interaction.id,
        payload={"from_stage_id": str(from_stage_id), "to_stage_code": to_stage.code},
    )


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


async def list_notes(
    session: AsyncSession, user: CurrentUser, interaction_id: uuid.UUID
) -> list[NoteOut]:
    await visible_interaction(session, user, interaction_id)
    rows = await session.execute(
        select(InteractionNote, AppUser)
        .join(AppUser, AppUser.id == InteractionNote.author_user_id)
        .where(InteractionNote.interaction_id == interaction_id)
        .order_by(InteractionNote.created_at.desc())
    )
    return [
        NoteOut(
            id=note.id,
            text=note.text,
            author=UserRef.model_validate(author),
            created_at=note.created_at,
        )
        for note, author in rows.tuples()
    ]


async def create_note(
    session: AsyncSession,
    user: CurrentUser,
    interaction_id: uuid.UUID,
    text: str,
    now: datetime | None = None,
) -> NoteOut:
    """Заметка — работа по взаимодействию, поэтому она же гасит сигнал о простое."""
    now = now or datetime.now(UTC)
    interaction = await visible_interaction(session, user, interaction_id)
    note = InteractionNote(interaction_id=interaction_id, author_user_id=user.id, text=text.strip())
    session.add(note)
    interaction.last_activity_at = now
    await session.flush()
    await recompute_signals(session, [interaction_id], now)
    await session.commit()
    return NoteOut(
        id=note.id,
        text=note.text,
        author=UserRef(id=user.id, full_name=user.full_name),
        created_at=note.created_at,
    )


async def _locked_interaction(
    session: AsyncSession, user: CurrentUser, interaction_id: uuid.UUID
) -> Interaction:
    """Запись в области видимости под блокировкой строки: параллельные изменения ждут очереди."""
    interaction = await session.scalar(
        apply_interaction_scope(
            select(Interaction).where(Interaction.id == interaction_id), user
        ).with_for_update()
    )
    if interaction is None:
        raise AppError(ErrorCode.NOT_FOUND, NOT_FOUND_DETAIL)
    return interaction


async def _bulk(
    session: AsyncSession,
    interaction_ids: list[uuid.UUID],
    one: Callable[[uuid.UUID], Coroutine[Any, Any, int]],
) -> BulkResult:
    """Каждая запись обрабатывается в своей точке сохранения, поэтому возможен частичный успех."""
    results: list[BulkItemResult] = []
    for interaction_id in dict.fromkeys(interaction_ids):
        try:
            async with session.begin_nested():
                version = await one(interaction_id)
        except AppError as error:
            results.append(
                BulkItemResult(
                    interaction_id=interaction_id, ok=False, code=error.code, detail=error.detail
                )
            )
        else:
            results.append(BulkItemResult(interaction_id=interaction_id, ok=True, version=version))
    await session.commit()
    succeeded = sum(1 for result in results if result.ok)
    return BulkResult(results=results, succeeded=succeeded, failed=len(results) - succeeded)


async def bulk_transitions(
    session: AsyncSession,
    user: CurrentUser,
    payload: BulkTransitionRequest,
    trace_id: str | None = None,
    now: datetime | None = None,
) -> BulkResult:
    moment = now or datetime.now(UTC)
    moved: Counter[uuid.UUID] = Counter()
    stage_name = ""

    async def move(interaction_id: uuid.UUID) -> int:
        nonlocal stage_name
        version, owner_id, stage_name = await _bulk_transition_one(
            session, user, interaction_id, payload, trace_id, moment
        )
        moved[owner_id] += 1
        return version

    result = await _bulk(session, payload.interaction_ids, move)
    await _notify_bulk_owners(session, user, moved, stage_name)
    return result


async def _notify_bulk_owners(
    session: AsyncSession, user: CurrentUser, moved: Counter[uuid.UUID], stage_name: str
) -> None:
    """Одно уведомление на владельца вместо сотни: групповой переход — одно действие."""
    for owner_id, count in moved.items():
        if owner_id == user.id:
            continue
        await notify(
            session,
            [owner_id],
            "stage_changed",
            f"Записи переведены на этап «{stage_name}»",
            f"{user.full_name} перевёл(а) групповым переходом ваших записей: {count}.",
            payload={"moved": count, "stage_name": stage_name},
        )
    if moved:
        await session.commit()


async def _bulk_transition_one(
    session: AsyncSession,
    user: CurrentUser,
    interaction_id: uuid.UUID,
    payload: BulkTransitionRequest,
    trace_id: str | None,
    now: datetime,
) -> tuple[int, uuid.UUID, str]:
    interaction = await _locked_interaction(session, user, interaction_id)
    if interaction.status != "active":
        raise AppError(ErrorCode.WF_TRANSITION_NOT_ALLOWED, "Взаимодействие не активно.")

    from_stage = await session.get(Stage, interaction.current_stage_id)
    if from_stage is None or not from_stage.bulk_allowed:
        name = from_stage.name if from_stage else "текущего"
        raise AppError(
            ErrorCode.WF_TRANSITION_NOT_ALLOWED,
            f"С этапа «{name}» групповой переход запрещён: переведите запись из карточки.",
        )
    to_stage = await session.scalar(
        select(Stage).where(
            Stage.version_id == interaction.workflow_version_id,
            Stage.code == payload.to_stage_code,
        )
    )
    rule = (
        await get_transition_rule(session, interaction.current_stage_id, to_stage.id)
        if to_stage is not None
        else None
    )
    if to_stage is None or rule is None:
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
    if rule.requires_attachment:
        # Документ прикладывается к конкретной записи, поэтому такой переход только из карточки.
        raise AppError(
            ErrorCode.WF_ATTACHMENT_REQUIRED,
            f"Переход на этап «{to_stage.name}» требует документа: выполните его в карточке.",
        )

    await _apply_transition(
        session,
        user,
        interaction,
        to_stage,
        comment,
        source="bulk",
        attachments=[],
        trace_id=trace_id,
        now=now,
        # Владельцу уходит одна сводка на весь групповой переход, а не письмо на каждую запись.
        notify_owner=False,
    )
    await recompute_signals(session, [interaction_id], now)
    return interaction.version, interaction.owner_user_id, to_stage.name


# Из какого состояния в какое можно перевести запись. Завершённую сначала возвращают в работу.
STATUS_FLOW: dict[str, tuple[str, ...]] = {
    "active": ("paused", "completed", "cancelled"),
    "paused": ("active", "completed", "cancelled"),
    "completed": ("active", "cancelled"),
    "cancelled": ("active",),
}
REASON_REQUIRED = ("paused", "cancelled")


async def change_status(
    session: AsyncSession,
    user: CurrentUser,
    interaction_id: uuid.UUID,
    payload: StatusChange,
    trace_id: str | None = None,
    now: datetime | None = None,
) -> InteractionDetail:
    """Пауза, завершение, отмена и возврат в работу: этап процесса и состояние записи — разное."""
    now = now or datetime.now(UTC)
    interaction = await _locked_interaction(session, user, interaction_id)
    if interaction.version != payload.expected_version:
        raise AppError(
            ErrorCode.INTERACTION_VERSION_CONFLICT,
            "Взаимодействие уже изменил другой пользователь. Обновите карточку и повторите.",
        )
    previous = interaction.status
    if payload.status == previous:
        return await get_interaction_detail(session, user, interaction_id, now)
    if payload.status not in STATUS_FLOW[previous]:
        was, becomes = STATUS_NAMES[previous], STATUS_NAMES[payload.status]
        raise AppError(
            ErrorCode.WF_TRANSITION_NOT_ALLOWED,
            f"Запись {was}: перевести её в состояние «{becomes}» нельзя.",
        )
    reason = payload.reason.strip()
    if payload.status in REASON_REQUIRED and not reason:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Объясните причину: она останется в истории записи.",
            errors=[FieldError(field="reason", message="Обязательное поле")],
        )
    if previous == "cancelled":
        # Отменённые не занимают связку: при возврате в работу она может быть уже занята.
        await _check_duplicate(session, interaction)

    interaction.status = payload.status
    interaction.last_activity_at = now
    interaction.version += 1
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="interaction.status_changed",
            entity_kind="interaction",
            entity_id=interaction.id,
            before={"status": previous},
            after={"status": payload.status, "reason": reason or None},
            trace_id=trace_id,
        )
    )
    try:
        # Проверка дубля выше конкурента не блокирует: последнее слово за уникальным индексом.
        async with session.begin_nested():
            await session.flush()
    except IntegrityError as error:
        raise AppError(
            ErrorCode.INTERACTION_DUPLICATE,
            "С этим контрагентом по этой программе и продукту уже ведётся другая запись.",
        ) from error
    # Неактивная запись не даёт сигналов: правила радара сами закроют открытые.
    await recompute_signals(session, [interaction.id], now)
    await mark_changed(session, [interaction.id], "status")
    if user.id != interaction.owner_user_id:
        label = await interaction_label(session, interaction.id)
        await notify(
            session,
            [interaction.owner_user_id],
            "stage_changed",
            f"Запись {STATUS_NAMES[payload.status]}: «{label}»",
            f"{user.full_name} изменил(а) состояние записи с «{STATUS_NAMES[previous]}» "
            f"на «{STATUS_NAMES[payload.status]}»." + (f" Причина: {reason}" if reason else ""),
            interaction_id=interaction.id,
            payload={"status": payload.status},
        )
    await session.commit()
    await get_event_bus().publish(
        INTERACTION_STATUS_CHANGED,
        {
            "interaction_id": str(interaction.id),
            "status": payload.status,
            "version": interaction.version,
        },
        owner_user_id=interaction.owner_user_id,
    )
    return await get_interaction_detail(session, user, interaction_id, now)


async def _check_duplicate(session: AsyncSession, interaction: Interaction) -> None:
    same_counterparty = (
        Interaction.university_id == interaction.university_id
        if interaction.university_id is not None
        else Interaction.client_id == interaction.client_id
    )
    duplicate = await session.scalar(
        select(Interaction.id).where(
            same_counterparty,
            Interaction.program_id == interaction.program_id,
            Interaction.product_id.is_not_distinct_from(interaction.product_id),
            Interaction.status != "cancelled",
            Interaction.id != interaction.id,
        )
    )
    if duplicate is not None:
        raise AppError(
            ErrorCode.INTERACTION_DUPLICATE,
            "С этим контрагентом по этой программе и продукту уже ведётся другая запись.",
        )


def _ensure_can_assign(user: CurrentUser) -> None:
    if user.role is Role.KAM:
        raise AppError(
            ErrorCode.AUTH_FORBIDDEN,
            "Менять ответственного может руководитель команды или администратор.",
        )


async def _assignable_user(
    session: AsyncSession, user: CurrentUser, owner_id: uuid.UUID
) -> AppUser:
    target = await session.scalar(select(AppUser).where(AppUser.id == owner_id))
    if target is None or not target.is_active:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Сотрудник не найден или отключён.",
            errors=[FieldError(field="owner_id", message="Неизвестный сотрудник")],
        )
    if user.role is Role.MANAGER and target.team_id != user.team_id:
        raise AppError(ErrorCode.AUTH_FORBIDDEN, "Назначить можно только сотрудника своей команды.")
    return target


async def _assign_owner(
    session: AsyncSession,
    user: CurrentUser,
    interaction: Interaction,
    target: AppUser,
    reason: str,
    trace_id: str | None,
    now: datetime,
) -> None:
    previous_owner_id = interaction.owner_user_id
    session.add(
        AssignmentChange(
            interaction_id=interaction.id,
            from_user_id=previous_owner_id,
            to_user_id=target.id,
            changed_by=user.id,
            changed_at=now,
            reason=reason or None,
        )
    )
    before = {"owner_user_id": str(previous_owner_id), "version": interaction.version}
    interaction.owner_user_id = target.id
    interaction.last_activity_at = now
    interaction.version += 1
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="interaction.owner_change",
            entity_kind="interaction",
            entity_id=interaction.id,
            before=before,
            after={"owner_user_id": str(target.id), "version": interaction.version},
            trace_id=trace_id,
        )
    )
    await session.flush()
    await mark_changed(session, [interaction.id], "owner")


async def change_owner(
    session: AsyncSession,
    user: CurrentUser,
    interaction_id: uuid.UUID,
    payload: OwnerChange,
    trace_id: str | None = None,
    now: datetime | None = None,
) -> InteractionDetail:
    now = now or datetime.now(UTC)
    _ensure_can_assign(user)
    interaction = await _locked_interaction(session, user, interaction_id)
    if interaction.version != payload.expected_version:
        raise AppError(
            ErrorCode.INTERACTION_VERSION_CONFLICT,
            "Взаимодействие уже изменил другой пользователь. Обновите карточку и повторите.",
        )
    target = await _assignable_user(session, user, payload.owner_id)
    if interaction.owner_user_id != target.id:
        reason = payload.reason.strip()
        await _assign_owner(session, user, interaction, target, reason, trace_id, now)
    await session.commit()
    return await get_interaction_detail(session, user, interaction_id, now)


async def bulk_change_owner(
    session: AsyncSession,
    user: CurrentUser,
    payload: BulkOwnerRequest,
    trace_id: str | None = None,
    now: datetime | None = None,
) -> BulkResult:
    moment = now or datetime.now(UTC)
    _ensure_can_assign(user)
    target = await _assignable_user(session, user, payload.owner_id)
    reason = payload.reason.strip()

    async def assign(interaction_id: uuid.UUID) -> int:
        interaction = await _locked_interaction(session, user, interaction_id)
        if interaction.owner_user_id != target.id:
            await _assign_owner(session, user, interaction, target, reason, trace_id, moment)
        return interaction.version

    return await _bulk(session, payload.interaction_ids, assign)
