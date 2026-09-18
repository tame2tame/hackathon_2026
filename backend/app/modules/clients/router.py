import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Query, status

from app.core.db import SessionDep
from app.core.errors import ErrorCode, TraceIdDep, error_responses
from app.core.pagination import Page, PageQuery
from app.core.security import CurrentUserDep
from app.modules.clients.schemas import ClientCreate, ClientListItem, ClientOut
from app.modules.clients.service import create_client, get_client, list_clients

router = APIRouter(prefix="/api/v1/clients", tags=["clients"])


@router.get(
    "",
    summary="Клиенты: физические и юридические лица",
    description=(
        "Организации видны всем. Людей видит тот, кто их завёл, владельцы их записей "
        "и руководитель команды. Email и телефон в списке не показываются."
    ),
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.VALIDATION_ERROR),
)
async def read_clients(
    session: SessionDep,
    user: CurrentUserDep,
    page: PageQuery,
    search: Annotated[
        str | None, Query(max_length=100, description="Имя, название или ИНН")
    ] = None,
    kind: Annotated[
        Literal["person", "organization"] | None, Query(description="Человек или организация")
    ] = None,
) -> Page[ClientListItem]:
    query = search.strip() if search and search.strip() else None
    return await list_clients(session, user, query, kind, page)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Добавить клиента",
    description="Email и телефон шифруются перед записью в базу; ИНН — только у организации.",
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.VALIDATION_ERROR),
)
async def post_client(
    payload: ClientCreate, trace_id: TraceIdDep, session: SessionDep, user: CurrentUserDep
) -> ClientOut:
    return await create_client(session, user, payload, trace_id)


@router.get(
    "/{client_id}",
    summary="Карточка клиента",
    description="Просмотр карточки человека пишется в аудит: это обращение к персональным данным.",
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND),
)
async def read_client(
    client_id: uuid.UUID, trace_id: TraceIdDep, session: SessionDep, user: CurrentUserDep
) -> ClientOut:
    return await get_client(session, user, client_id, trace_id)
