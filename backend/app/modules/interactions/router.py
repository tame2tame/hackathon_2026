import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.core.db import SessionDep
from app.core.errors import ErrorCode, error_responses
from app.core.pagination import Page, PageQuery
from app.core.security import CurrentUserDep
from app.modules.interactions.schemas import (
    BulkOwnerRequest,
    BulkResult,
    BulkTransitionRequest,
    InteractionDetail,
    InteractionListItem,
    OwnerChange,
    TransitionCreate,
    TransitionResult,
)
from app.modules.interactions.service import (
    InteractionFilters,
    bulk_change_owner,
    bulk_transitions,
    change_owner,
    create_transition,
    get_interaction_detail,
    list_interactions,
)

router = APIRouter(prefix="/api/v1/interactions", tags=["interactions"])


def _interaction_filters(
    university_id: Annotated[list[uuid.UUID] | None, Query(description="Вуз")] = None,
    direction_id: Annotated[list[uuid.UUID] | None, Query(description="ИТ-направление")] = None,
    program_id: Annotated[list[uuid.UUID] | None, Query(description="ИТ-программа")] = None,
    product_id: Annotated[list[uuid.UUID] | None, Query(description="ИТ-продукт")] = None,
    owner_id: Annotated[list[uuid.UUID] | None, Query(description="КАМ")] = None,
    stage_code: Annotated[list[str] | None, Query(description="Код текущего этапа")] = None,
    has_signal: Annotated[bool | None, Query(description="Есть открытый сигнал")] = None,
    period_from: Annotated[date | None, Query(description="Начало периода, UTC")] = None,
    period_to: Annotated[date | None, Query(description="Конец периода, UTC")] = None,
    search: Annotated[
        str | None, Query(max_length=100, description="Вуз, программа или продукт")
    ] = None,
) -> InteractionFilters:
    return InteractionFilters(
        university_id=university_id or [],
        direction_id=direction_id or [],
        program_id=program_id or [],
        product_id=product_id or [],
        owner_id=owner_id or [],
        stage_code=stage_code or [],
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


@router.get(
    "/{interaction_id}",
    summary="Карточка взаимодействия",
    description="История, допустимые переходы с требованиями и открытые сигналы.",
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND),
)
async def read_interaction(
    interaction_id: uuid.UUID, session: SessionDep, user: CurrentUserDep
) -> InteractionDetail:
    return await get_interaction_detail(session, user, interaction_id)


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
    request: Request,
    session: SessionDep,
    user: CurrentUserDep,
) -> TransitionResult:
    trace_id = getattr(request.state, "trace_id", None)
    return await create_transition(session, user, interaction_id, payload, trace_id=trace_id)


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
    request: Request,
    session: SessionDep,
    user: CurrentUserDep,
) -> BulkResult:
    trace_id = getattr(request.state, "trace_id", None)
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
    request: Request,
    session: SessionDep,
    user: CurrentUserDep,
) -> InteractionDetail:
    trace_id = getattr(request.state, "trace_id", None)
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
    request: Request,
    session: SessionDep,
    user: CurrentUserDep,
) -> BulkResult:
    trace_id = getattr(request.state, "trace_id", None)
    return await bulk_change_owner(session, user, payload, trace_id=trace_id)
