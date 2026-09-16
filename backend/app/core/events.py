"""События для SSE: поток в Redis и та же логика в памяти, когда Redis не нужен.

Читатель всегда двигается по курсору, поэтому переподключение с `Last-Event-ID` досылает
пропущенное. Длина потока ограничена: история событий нужна на минуты, а не навсегда.
"""

import asyncio
import json
import uuid
from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Protocol

from redis.asyncio import Redis

from app.core.config import get_settings

STREAM_KEY = "radar:events"
STREAM_MAXLEN = 1000
HEARTBEAT_SECONDS = 15

INTERACTION_TRANSITIONED = "interaction.transitioned"
SIGNAL_OPENED = "signal.opened"
SIGNAL_RESOLVED = "signal.resolved"
IMPORT_APPLIED = "import.applied"
REPORT_UPDATED = "report.updated"

EVENT_KINDS = (
    INTERACTION_TRANSITIONED,
    SIGNAL_OPENED,
    SIGNAL_RESOLVED,
    IMPORT_APPLIED,
    REPORT_UPDATED,
)


@dataclass(frozen=True, slots=True)
class Event:
    """Событие с адресом: по владельцу и его команде решается, кому его показывать."""

    id: str
    kind: str
    payload: dict[str, Any]
    owner_user_id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None

    def to_sse(self) -> str:
        data = json.dumps(self.payload, ensure_ascii=False)
        return f"id: {self.id}\nevent: {self.kind}\ndata: {data}\n\n"


class EventBus(Protocol):
    async def publish(
        self,
        kind: str,
        payload: dict[str, Any],
        *,
        owner_user_id: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
    ) -> Event: ...

    async def read(self, cursor: str | None, timeout_ms: int) -> tuple[list[Event], str | None]: ...


def _encode(event: Event) -> dict[Any, Any]:
    """Поля записи в потоке Redis: клиент принимает скалярные значения любого типа."""
    return {
        "kind": event.kind,
        "payload": json.dumps(event.payload, ensure_ascii=False),
        "owner_user_id": str(event.owner_user_id or ""),
        "team_id": str(event.team_id or ""),
    }


def _decode(event_id: str, fields: dict[str, str]) -> Event:
    return Event(
        id=event_id,
        kind=fields["kind"],
        payload=json.loads(fields["payload"]),
        owner_user_id=uuid.UUID(fields["owner_user_id"]) if fields.get("owner_user_id") else None,
        team_id=uuid.UUID(fields["team_id"]) if fields.get("team_id") else None,
    )


class MemoryEventBus:
    """События в памяти процесса: для тестов и запуска без Redis."""

    def __init__(self, maxlen: int = STREAM_MAXLEN) -> None:
        self._events: deque[Event] = deque(maxlen=maxlen)
        self._arrived = asyncio.Condition()
        self._counter = 0

    async def publish(
        self,
        kind: str,
        payload: dict[str, Any],
        *,
        owner_user_id: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
    ) -> Event:
        async with self._arrived:
            self._counter += 1
            event = Event(str(self._counter), kind, payload, owner_user_id, team_id)
            self._events.append(event)
            self._arrived.notify_all()
        return event

    async def read(self, cursor: str | None, timeout_ms: int) -> tuple[list[Event], str | None]:
        # Без курсора читатель получает только новые события, как XREAD с «$».
        position = int(cursor) if cursor else self._counter
        pending = [event for event in self._events if int(event.id) > position]
        if pending:
            return pending, pending[-1].id
        async with self._arrived:
            try:
                await asyncio.wait_for(self._arrived.wait(), timeout_ms / 1000)
            except TimeoutError:
                return [], str(position)
        pending = [event for event in self._events if int(event.id) > position]
        return pending, pending[-1].id if pending else str(position)


class RedisEventBus:
    """Поток Redis: события переживают перезапуск процесса и видны всем экземплярам API."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def publish(
        self,
        kind: str,
        payload: dict[str, Any],
        *,
        owner_user_id: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
    ) -> Event:
        event = Event("", kind, payload, owner_user_id, team_id)
        event_id = await self._client.xadd(
            STREAM_KEY, _encode(event), maxlen=STREAM_MAXLEN, approximate=True
        )
        return Event(str(event_id), kind, payload, owner_user_id, team_id)

    async def read(self, cursor: str | None, timeout_ms: int) -> tuple[list[Event], str | None]:
        start = cursor or "$"
        response = await self._client.xread({STREAM_KEY: start}, count=100, block=timeout_ms)
        if not response:
            return [], cursor
        _, entries = response[0]
        events = [_decode(str(event_id), fields) for event_id, fields in entries]
        return events, events[-1].id if events else cursor


@lru_cache
def get_event_bus() -> EventBus:
    settings = get_settings()
    if settings.app_env == "test" or not settings.redis_url:
        return MemoryEventBus()
    return RedisEventBus(Redis.from_url(settings.redis_url, decode_responses=True))
