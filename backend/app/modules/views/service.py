"""Сохранённые виды: свои у каждого пользователя.

Сервер не разбирает фильтры: что означает `stage_code` или `days_on_stage`, знает страница.
Он только хранит их под названием и следит, чтобы в базу не попал мусор вместо настроек.
"""

import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ErrorCode, FieldError
from app.core.security import CurrentUser
from app.modules.views.models import SavedView
from app.modules.views.schemas import (
    MAX_FILTERS_BYTES,
    SavedViewCreate,
    SavedViewOut,
    SavedViewUpdate,
)

NOT_FOUND = "Сохранённый вид не найден."


def _check_size(filters: dict[str, object]) -> None:
    if len(json.dumps(filters, ensure_ascii=False).encode()) > MAX_FILTERS_BYTES:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Слишком много фильтров: вид хранит настройки списка, а не сами данные.",
            errors=[FieldError(field="filters", message="Не больше 4 КБ")],
        )


async def _taken(
    session: AsyncSession, user: CurrentUser, page: str, name: str, skip: uuid.UUID | None = None
) -> bool:
    stmt = select(SavedView.id).where(
        SavedView.user_id == user.id, SavedView.page == page, SavedView.name == name
    )
    if skip is not None:
        stmt = stmt.where(SavedView.id != skip)
    return await session.scalar(stmt) is not None


async def list_views(
    session: AsyncSession, user: CurrentUser, page: str | None = None
) -> list[SavedViewOut]:
    stmt = (
        select(SavedView)
        .where(SavedView.user_id == user.id)
        .order_by(SavedView.page, SavedView.name)
    )
    if page:
        stmt = stmt.where(SavedView.page == page)
    return [SavedViewOut.model_validate(view) for view in await session.scalars(stmt)]


async def create_view(
    session: AsyncSession, user: CurrentUser, payload: SavedViewCreate
) -> SavedViewOut:
    name = payload.name.strip()
    _check_size(payload.filters)
    if await _taken(session, user, payload.page, name):
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Вид с таким названием уже сохранён: выберите другое название.",
            errors=[FieldError(field="name", message="Название занято")],
        )
    view = SavedView(
        user_id=user.id,
        page=payload.page,
        name=name,
        filters=payload.filters,
        columns=payload.columns,
    )
    session.add(view)
    await session.commit()
    return SavedViewOut.model_validate(view)


async def _own(session: AsyncSession, user: CurrentUser, view_id: uuid.UUID) -> SavedView:
    view = await session.scalar(
        select(SavedView).where(SavedView.id == view_id, SavedView.user_id == user.id)
    )
    if view is None:
        raise AppError(ErrorCode.NOT_FOUND, NOT_FOUND)
    return view


async def update_view(
    session: AsyncSession, user: CurrentUser, view_id: uuid.UUID, payload: SavedViewUpdate
) -> SavedViewOut:
    view = await _own(session, user, view_id)
    if payload.name is not None:
        name = payload.name.strip()
        if await _taken(session, user, view.page, name, skip=view.id):
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Вид с таким названием уже сохранён: выберите другое название.",
                errors=[FieldError(field="name", message="Название занято")],
            )
        view.name = name
    if payload.filters is not None:
        _check_size(payload.filters)
        view.filters = payload.filters
    if payload.columns is not None:
        view.columns = payload.columns
    await session.commit()
    # `updated_at` проставляет база: без обновления объекта его ещё нет.
    await session.refresh(view)
    return SavedViewOut.model_validate(view)


async def delete_view(session: AsyncSession, user: CurrentUser, view_id: uuid.UUID) -> None:
    view = await _own(session, user, view_id)
    await session.delete(view)
    await session.commit()
