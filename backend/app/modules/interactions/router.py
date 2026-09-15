import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.core.db import SessionDep
from app.core.errors import ErrorCode, error_responses
from app.core.pagination import Page, PageQuery
from app.core.security import CurrentUserDep
from app.modules.interactions.schemas import (
    InteractionDetail,
    InteractionListItem,
    TransitionCreate,
    TransitionResult,
)
from app.modules.interactions.service import (
    InteractionFilters,
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
        ErrorCode.INTERACTION_VERSION_CONFLICT,
        ErrorCode.WF_COMMENT_REQUIRED,
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
