"""Поток событий SSE: клиент получает только то, что ему положено видеть.

Поток живёт часами, поэтому соединение с базой он держит только на миг: сессия запроса
закрывается до начала потока, а проверки прав идут короткими сессиями. Иначе пятнадцать
открытых вкладок забирали бы весь пул, и остальной API отвечал бы 500.
"""

import uuid
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Header, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.core.db import SessionDep, SessionFactory, SessionFactoryDep
from app.core.errors import ErrorCode, error_responses
from app.core.events import (
    HEARTBEAT_SECONDS,
    MESSAGE_CREATED,
    NOTIFICATION_CREATED,
    REPORT_UPDATED,
    Event,
    get_event_bus,
)
from app.core.roles import Role
from app.core.scope import apply_interaction_scope
from app.core.security import CurrentUser, CurrentUserDep, current_user_for
from app.modules.catalogs.models import AppUser
from app.modules.interactions.models import Interaction

router = APIRouter(prefix="/api/v1", tags=["events"])

# Личные события: их не видит даже администратор — ни уведомление, ни переписка.
PERSONAL = frozenset({NOTIFICATION_CREATED, MESSAGE_CREATED})
# Сколько пульсов между перепроверками пользователя: отключённый сотрудник теряет поток
# примерно через минуту, а не при обрыве связи.
RECHECK_EVERY = 4


def interaction_of(event: Event) -> uuid.UUID | None:
    value = event.payload.get("interaction_id")
    try:
        return uuid.UUID(str(value)) if value else None
    except ValueError:
        return None


def visible(
    event: Event,
    user: CurrentUser,
    team_members: set[uuid.UUID],
    allowed: set[uuid.UUID] | None = None,
) -> bool:
    """Та же область видимости, что у списков.

    `allowed` — записи, которые пользователь видит по области видимости и правилам доступа
    администратора. Если событие о записи, решает именно он: запрет администратора действует
    и в потоке, а не только в списках.
    """
    if event.kind in PERSONAL:
        return event.owner_user_id == user.id
    if event.kind == REPORT_UPDATED:
        return event.owner_user_id == user.id or user.role is Role.ADMIN
    interaction_id = interaction_of(event)
    if allowed is not None and interaction_id is not None:
        return interaction_id in allowed
    if user.role is Role.ADMIN:
        return True
    if event.owner_user_id is None:
        # Общие события (импорт) не адресованы КАМу конкретной записи.
        return user.role is Role.MANAGER
    if event.owner_user_id == user.id:
        return True
    return user.role is Role.MANAGER and event.owner_user_id in team_members


async def _refresh(factory: SessionFactory, user_id: uuid.UUID) -> CurrentUser | None:
    """Пользователь с актуальными ролью, командой и правилами; отключённый — None."""
    async with factory() as session:
        found = await session.get(AppUser, user_id)
        if found is None or not found.is_active:
            return None
        return await current_user_for(session, found)


async def _team(factory: SessionFactory, user: CurrentUser) -> set[uuid.UUID]:
    if user.role is not Role.MANAGER or user.team_id is None:
        return set()
    async with factory() as session:
        members = await session.scalars(select(AppUser.id).where(AppUser.team_id == user.team_id))
        return set(members)


async def _allowed(
    factory: SessionFactory, user: CurrentUser, events: list[Event]
) -> set[uuid.UUID]:
    wanted = {item for item in map(interaction_of, events) if item is not None}
    if not wanted:
        return set()
    async with factory() as session:
        rows = await session.scalars(
            apply_interaction_scope(select(Interaction.id).where(Interaction.id.in_(wanted)), user)
        )
        return set(rows)


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
    factory: SessionFactoryDep,
    user: CurrentUserDep,
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
) -> StreamingResponse:
    bus = get_event_bus()
    # Сессия запроса нужна была только для входа: отдаём соединение в пул до начала потока.
    await session.close()

    async def stream() -> AsyncIterator[str]:
        current = user
        team_members = await _team(factory, current)
        cursor = last_event_id
        beats = 0
        yield ": подключено\n\n"
        while not await request.is_disconnected():
            events, cursor = await bus.read(cursor, HEARTBEAT_SECONDS * 1000)
            if not events:
                beats += 1
                if beats % RECHECK_EVERY == 0:
                    refreshed = await _refresh(factory, current.id)
                    if refreshed is None:
                        # Сотрудника отключили: поток закрывается, а не досылает события.
                        return
                    current = refreshed
                    team_members = await _team(factory, current)
                yield ": пульс\n\n"
                continue
            allowed = await _allowed(factory, current, events)
            for event in events:
                if visible(event, current, team_members, allowed):
                    yield event.to_sse()

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
