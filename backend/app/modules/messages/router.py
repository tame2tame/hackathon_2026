import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.db import SessionDep
from app.core.errors import ErrorCode, error_responses
from app.core.security import CurrentUserDep
from app.modules.messages.schemas import DialogsOut, MessageCreate, MessageOut, ReadOut
from app.modules.messages.service import list_dialogs, mark_read, read_dialog, send_message

router = APIRouter(prefix="/api/v1/messages", tags=["messages"])
PEER_ERRORS = error_responses(
    ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND, ErrorCode.VALIDATION_ERROR
)


@router.get(
    "",
    summary="Мои переписки",
    description=(
        "С кем шла переписка, последнее сообщение и сколько сообщений не прочитано. "
        "Общее число непрочитанных — `unread_total`, для значка в шапке."
    ),
    responses=error_responses(ErrorCode.AUTH_REQUIRED),
)
async def read_dialogs(session: SessionDep, user: CurrentUserDep) -> DialogsOut:
    return await list_dialogs(session, user)


@router.get(
    "/{peer_id}",
    summary="Переписка с сотрудником",
    description="Сначала старые сообщения. Чужую переписку не покажет: видно только свою.",
    responses=PEER_ERRORS,
)
async def read_messages(
    peer_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUserDep,
    limit: Annotated[int, Query(ge=1, le=200, description="Сколько последних сообщений")] = 50,
) -> list[MessageOut]:
    return await read_dialog(session, user, peer_id, limit)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Написать сотруднику",
    description=(
        "Сообщение видят только двое. Можно сослаться на свою запись: собеседник увидит ссылку, "
        "если запись доступна и ему."
    ),
    responses=PEER_ERRORS,
)
async def post_message(
    payload: MessageCreate, session: SessionDep, user: CurrentUserDep
) -> MessageOut:
    return await send_message(session, user, payload)


@router.post(
    "/{peer_id}/read",
    summary="Отметить переписку прочитанной",
    responses=PEER_ERRORS,
)
async def post_read(peer_id: uuid.UUID, session: SessionDep, user: CurrentUserDep) -> ReadOut:
    return ReadOut(updated=await mark_read(session, user, peer_id))
