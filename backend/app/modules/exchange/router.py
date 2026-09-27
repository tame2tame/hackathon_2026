import uuid
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.core.db import SessionDep
from app.core.errors import ErrorCode, error_responses
from app.core.pagination import Page, PageQuery
from app.core.scope import apply_interaction_scope, visible_interaction
from app.core.security import CurrentUserDep
from app.modules.exchange.documents import build_documents
from app.modules.exchange.schemas import InteractionDocument
from app.modules.interactions.models import Interaction

router = APIRouter(prefix="/api/v1", tags=["exchange"])

# `updated_at` — время начала транзакции, а не её фиксации: запись, зафиксированная сразу после
# опроса, может получить время раньше него и выпасть из следующего. Поэтому окно перекрывается:
# повтор последних минут безвреден (документ идемпотентен по id), а пропуск — нет. Транзакции
# запросов короче минуты, пять минут — с запасом.
EXCHANGE_OVERLAP = timedelta(minutes=5)


@router.get(
    "/interactions/{interaction_id}/export",
    summary="Документ обмена по записи",
    description=(
        "JSON `radar-vuzov/interaction@1`: статус, ответственный, контрагент, программа, продукт "
        "и ключи связей с записями базы и файлами в S3. Тот же документ уходит в LMS и CMS."
    ),
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND),
)
async def read_interaction_document(
    interaction_id: uuid.UUID, session: SessionDep, user: CurrentUserDep
) -> InteractionDocument:
    await visible_interaction(session, user, interaction_id)
    [document] = await build_documents(session, [interaction_id])
    return document


@router.get(
    "/exchange/interactions",
    summary="Выгрузка записей в JSON",
    description=(
        "Документы `radar-vuzov/interaction@1` в области видимости пользователя. `updated_since` "
        "отдаёт только изменённые с этого момента — так внешняя система забирает изменения "
        "по расписанию, не перечитывая всё. Окно перекрывается на пять минут назад: запись, "
        "зафиксированная во время прошлого опроса, придёт в следующем. Повтор документа "
        "обрабатывается по `record.id` и `record.updated_at`."
    ),
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.VALIDATION_ERROR),
)
async def read_exchange(
    session: SessionDep,
    user: CurrentUserDep,
    page: PageQuery,
    updated_since: Annotated[
        datetime | None, Query(description="Изменённые не раньше этого момента, ISO 8601")
    ] = None,
    group_id: Annotated[list[uuid.UUID] | None, Query(description="Группа контрагентов")] = None,
) -> Page[InteractionDocument]:
    stmt = apply_interaction_scope(select(Interaction.id), user)
    if updated_since is not None:
        stmt = stmt.where(Interaction.updated_at >= updated_since - EXCHANGE_OVERLAP)
    if group_id:
        stmt = stmt.where(Interaction.group_id.in_(group_id))
    total = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    ids = list(
        await session.scalars(
            stmt.order_by(Interaction.updated_at, Interaction.id)
            .offset(page.offset)
            .limit(page.page_size)
        )
    )
    return Page(
        items=await build_documents(session, ids),
        total=total,
        page=page.page,
        page_size=page.page_size,
    )
