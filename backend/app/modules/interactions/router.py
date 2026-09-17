import uuid
from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Request, Response, status

from app.core.db import SessionDep
from app.core.errors import ErrorCode, TraceIdDep, error_responses
from app.core.http_cache import NOT_MODIFIED_RESPONSE, conditional
from app.core.pagination import Page, PageQuery
from app.core.security import CurrentUserDep
from app.modules.interactions.schemas import (
    BulkOwnerRequest,
    BulkResult,
    BulkTransitionRequest,
    InteractionCreate,
    InteractionDetail,
    InteractionListItem,
    NoteCreate,
    NoteOut,
    OwnerChange,
    StatusChange,
    TransitionCreate,
    TransitionResult,
)
from app.modules.interactions.service import (
    InteractionFilters,
    bulk_change_owner,
    bulk_transitions,
    change_owner,
    change_status,
    create_interaction,
    create_note,
    create_transition,
    get_interaction_detail,
    list_interactions,
    list_notes,
)

router = APIRouter(prefix="/api/v1/interactions", tags=["interactions"])


def _interaction_filters(
    group_id: Annotated[list[uuid.UUID] | None, Query(description="Группа контрагентов")] = None,
    client_id: Annotated[list[uuid.UUID] | None, Query(description="Клиент вне вузов")] = None,
    university_id: Annotated[list[uuid.UUID] | None, Query(description="Вуз")] = None,
    direction_id: Annotated[list[uuid.UUID] | None, Query(description="ИТ-направление")] = None,
    program_id: Annotated[list[uuid.UUID] | None, Query(description="ИТ-программа")] = None,
    product_id: Annotated[list[uuid.UUID] | None, Query(description="ИТ-продукт")] = None,
    owner_id: Annotated[list[uuid.UUID] | None, Query(description="КАМ")] = None,
    stage_code: Annotated[list[str] | None, Query(description="Код текущего этапа")] = None,
    status: Annotated[
        list[Literal["active", "paused", "completed", "cancelled"]] | None,
        Query(description="Состояние записи; без фильтра отменённые скрыты"),
    ] = None,
    has_signal: Annotated[bool | None, Query(description="Есть открытый сигнал")] = None,
    period_from: Annotated[date | None, Query(description="Начало периода, UTC")] = None,
    period_to: Annotated[date | None, Query(description="Конец периода, UTC")] = None,
    search: Annotated[
        str | None, Query(max_length=100, description="Контрагент, программа или продукт")
    ] = None,
) -> InteractionFilters:
    return InteractionFilters(
        group_id=group_id or [],
        client_id=client_id or [],
        university_id=university_id or [],
        direction_id=direction_id or [],
        program_id=program_id or [],
        product_id=product_id or [],
        owner_id=owner_id or [],
        stage_code=stage_code or [],
        status=list(status or []),
        has_signal=has_signal,
        period_from=period_from,
        period_to=period_to,
        search=search.strip() if search and search.strip() else None,
    )


@router.get(
    "",
    summary="Взаимодействия с фильтрами",
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.VALIDATION_ERROR),
)
async def read_interactions(
    session: SessionDep,
    user: CurrentUserDep,
    page: PageQuery,
    filters: Annotated[InteractionFilters, Depends(_interaction_filters)],
) -> Page[InteractionListItem]:
    return await list_interactions(session, user, filters, page)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Завести взаимодействие вручную",
    description=(
        "Запись встаёт на первый этап процесса своей группы. Контрагент — ровно один: вуз или "
        "клиент. Продуктозависимой программе нужен её продукт. Назначить другого ответственного "
        "может руководитель в пределах команды или администратор."
    ),
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED,
        ErrorCode.AUTH_FORBIDDEN,
        ErrorCode.NOT_FOUND,
        ErrorCode.VALIDATION_ERROR,
        ErrorCode.INTERACTION_DUPLICATE,
    ),
)
async def post_interaction(
    payload: InteractionCreate,
    trace_id: TraceIdDep,
    session: SessionDep,
    user: CurrentUserDep,
) -> InteractionDetail:
    return await create_interaction(session, user, payload, trace_id=trace_id)


@router.get(
    "/{interaction_id}",
    summary="Карточка взаимодействия",
    description=(
        "История, допустимые переходы с требованиями и открытые сигналы. Ответ помечен ETag: "
        "открытая заново карточка достаётся из кэша браузера, если на сервере ничего не менялось."
    ),
    response_model=InteractionDetail,
    responses={
        **error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND),
        **NOT_MODIFIED_RESPONSE,
    },
)
async def read_interaction(
    request: Request, interaction_id: uuid.UUID, session: SessionDep, user: CurrentUserDep
) -> Response:
    card = await get_interaction_detail(session, user, interaction_id)
    return conditional(request, card.model_dump_json().encode())


@router.post(
    "/{interaction_id}/transitions",
    status_code=status.HTTP_201_CREATED,
    summary="Перевести взаимодействие на другой этап",
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED,
        ErrorCode.NOT_FOUND,
        ErrorCode.VALIDATION_ERROR,
        ErrorCode.INTERACTION_VERSION_CONFLICT,
        ErrorCode.WF_TRANSITION_NOT_ALLOWED,
        ErrorCode.WF_COMMENT_REQUIRED,
        ErrorCode.WF_ATTACHMENT_REQUIRED,
    ),
)
async def post_transition(
    interaction_id: uuid.UUID,
    payload: TransitionCreate,
    trace_id: TraceIdDep,
    session: SessionDep,
    user: CurrentUserDep,
) -> TransitionResult:
    return await create_transition(session, user, interaction_id, payload, trace_id=trace_id)


@router.get(
    "/{interaction_id}/notes",
    summary="Заметки по взаимодействию",
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND),
)
async def read_notes(
    interaction_id: uuid.UUID, session: SessionDep, user: CurrentUserDep
) -> list[NoteOut]:
    return await list_notes(session, user, interaction_id)


@router.post(
    "/{interaction_id}/notes",
    status_code=status.HTTP_201_CREATED,
    summary="Добавить заметку",
    description="Заметка считается работой по записи и снимает сигнал о простое.",
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND, ErrorCode.VALIDATION_ERROR
    ),
)
async def post_note(
    interaction_id: uuid.UUID,
    payload: NoteCreate,
    session: SessionDep,
    user: CurrentUserDep,
) -> NoteOut:
    return await create_note(session, user, interaction_id, payload.text)


@router.put(
    "/{interaction_id}/status",
    summary="Приостановить, завершить, отменить или вернуть запись в работу",
    description=(
        "Состояние записи ставит человек: финальный этап сам по себе ничего не завершает. "
        "Для паузы и отмены нужна причина — она остаётся в аудите. Неактивная запись не даёт "
        "сигналов радара и не принимает переходы. Возврат отменённой в работу невозможен, если "
        "такую же связку уже ведёт другая запись."
    ),
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED,
        ErrorCode.NOT_FOUND,
        ErrorCode.VALIDATION_ERROR,
        ErrorCode.INTERACTION_VERSION_CONFLICT,
        ErrorCode.INTERACTION_DUPLICATE,
        ErrorCode.WF_TRANSITION_NOT_ALLOWED,
    ),
)
async def put_status(
    interaction_id: uuid.UUID,
    payload: StatusChange,
    trace_id: TraceIdDep,
    session: SessionDep,
    user: CurrentUserDep,
) -> InteractionDetail:
    return await change_status(session, user, interaction_id, payload, trace_id=trace_id)


@router.post(
    "/bulk-transitions",
    summary="Перевести несколько взаимодействий на один этап",
    description=(
        "Разрешён только с этапов с `bulk_allowed`. У каждой записи свой итог, "
        "поэтому частичный успех — обычный ответ. Переход с требованием документа "
        "выполняется в карточке."
    ),
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED,
        ErrorCode.VALIDATION_ERROR,
    ),
)
async def post_bulk_transitions(
    payload: BulkTransitionRequest,
    trace_id: TraceIdDep,
    session: SessionDep,
    user: CurrentUserDep,
) -> BulkResult:
    return await bulk_transitions(session, user, payload, trace_id=trace_id)


@router.put(
    "/{interaction_id}/owner",
    summary="Сменить ответственного КАМа",
    description="Доступно руководителю в пределах команды и администратору.",
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED,
        ErrorCode.AUTH_FORBIDDEN,
        ErrorCode.NOT_FOUND,
        ErrorCode.VALIDATION_ERROR,
        ErrorCode.INTERACTION_VERSION_CONFLICT,
    ),
)
async def put_owner(
    interaction_id: uuid.UUID,
    payload: OwnerChange,
    trace_id: TraceIdDep,
    session: SessionDep,
    user: CurrentUserDep,
) -> InteractionDetail:
    return await change_owner(session, user, interaction_id, payload, trace_id=trace_id)


@router.post(
    "/bulk-owner",
    summary="Передать несколько взаимодействий другому КАМу",
    description="Итог по каждой записи; недоступные записи возвращают `NOT_FOUND`.",
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED,
        ErrorCode.AUTH_FORBIDDEN,
        ErrorCode.VALIDATION_ERROR,
    ),
)
async def post_bulk_owner(
    payload: BulkOwnerRequest,
    trace_id: TraceIdDep,
    session: SessionDep,
    user: CurrentUserDep,
) -> BulkResult:
    return await bulk_change_owner(session, user, payload, trace_id=trace_id)
