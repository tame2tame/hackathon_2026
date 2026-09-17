import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.db import SessionDep
from app.core.errors import ErrorCode, error_responses
from app.core.security import CurrentUserDep
from app.modules.views.schemas import SavedViewCreate, SavedViewOut, SavedViewUpdate, ViewPage
from app.modules.views.service import create_view, delete_view, list_views, update_view

router = APIRouter(prefix="/api/v1/saved-views", tags=["saved-views"])
OWN_ERRORS = error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND)


@router.get(
    "",
    summary="Мои сохранённые виды",
    description="Набор фильтров и колонок под своим названием. Виды свои у каждого.",
    responses=error_responses(ErrorCode.AUTH_REQUIRED),
)
async def read_views(
    session: SessionDep,
    user: CurrentUserDep,
    page: Annotated[ViewPage | None, Query(description="Только для одной страницы")] = None,
) -> list[SavedViewOut]:
    return await list_views(session, user, page)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Сохранить вид",
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.VALIDATION_ERROR),
)
async def post_view(
    payload: SavedViewCreate, session: SessionDep, user: CurrentUserDep
) -> SavedViewOut:
    return await create_view(session, user, payload)


@router.patch(
    "/{view_id}",
    summary="Изменить сохранённый вид",
    description="Название, фильтры или колонки. Пропущенное поле остаётся как было.",
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND, ErrorCode.VALIDATION_ERROR
    ),
)
async def patch_view(
    view_id: uuid.UUID, payload: SavedViewUpdate, session: SessionDep, user: CurrentUserDep
) -> SavedViewOut:
    return await update_view(session, user, view_id, payload)


@router.delete(
    "/{view_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить сохранённый вид",
    responses=OWN_ERRORS,
)
async def remove_view(view_id: uuid.UUID, session: SessionDep, user: CurrentUserDep) -> None:
    await delete_view(session, user, view_id)
