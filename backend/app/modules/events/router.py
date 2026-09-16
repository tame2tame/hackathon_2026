"""Поток событий SSE: клиент получает только то, что ему положено видеть."""

import uuid
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Header, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import SessionDep
from app.core.errors import ErrorCode, error_responses
from app.core.events import HEARTBEAT_SECONDS, Event, get_event_bus
from app.core.roles import Role
from app.core.security import CurrentUser, CurrentUserDep
from app.modules.catalogs.models import AppUser

router = APIRouter(prefix="/api/v1", tags=["events"])


async def team_member_ids(session: AsyncSession, user: CurrentUser) -> set[uuid.UUID]:
    if user.role is not Role.MANAGER or user.team_id is None:
        return set()
    members = await session.scalars(select(AppUser.id).where(AppUser.team_id == user.team_id))
    return set(members)


def visible(event: Event, user: CurrentUser, team_members: set[uuid.UUID]) -> bool:
    """Та же область видимости, что у списков: КАМ видит своё, руководитель — команду."""
    if user.role is Role.ADMIN:
        return True
    if event.owner_user_id is None:
        # Общие события (импорт, отчёты) не адресованы КАМу конкретной записи.
        return user.role is Role.MANAGER
    if event.owner_user_id == user.id:
        return True
    return user.role is Role.MANAGER and event.owner_user_id in team_members


@router.get(
    "/events",
    summary="Поток событий",
    description=(
        "`text/event-stream`. Заголовок `Last-Event-ID` досылает пропущенное после обрыва связи; "
        f"раз в {HEARTBEAT_SECONDS} секунд приходит комментарий-пульс."
    ),
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": "События области видимости пользователя",
        },
        **error_responses(ErrorCode.AUTH_REQUIRED),
    },
)
async def read_events(
    request: Request,
    session: SessionDep,
    user: CurrentUserDep,
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
) -> StreamingResponse:
    bus = get_event_bus()
    team_members = await team_member_ids(session, user)

    async def stream() -> AsyncIterator[str]:
        cursor = last_event_id
        yield ": подключено\n\n"
        while not await request.is_disconnected():
            events, cursor = await bus.read(cursor, HEARTBEAT_SECONDS * 1000)
            if not events:
                yield ": пульс\n\n"
                continue
            for event in events:
                if visible(event, user, team_members):
                    yield event.to_sse()

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
