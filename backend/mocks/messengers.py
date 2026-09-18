"""Заглушка мессенджеров: Telegram Bot API (`sendMessage`) и Bot API Max (`messages`).

Принимает сообщения так же, как настоящие сервисы, и показывает полученное на `GET /sent`:
на стенде видно, что уведомление действительно ушло.
Запуск: `uvicorn mocks.messengers:app --port 8102`.
"""

from datetime import UTC, datetime
from itertools import count
from typing import Annotated, Any

from fastapi import Body, FastAPI, Query

app = FastAPI(title="Заглушка мессенджеров", docs_url="/docs")

_sent: list[dict[str, Any]] = []
_ids = count(1)


def _store(channel: str, address: str, text: str) -> dict[str, Any]:
    message = {
        "id": next(_ids),
        "channel": channel,
        "address": address,
        "text": text,
        "received_at": datetime.now(UTC).isoformat(),
    }
    _sent.append(message)
    return message


@app.post("/bot{token}/sendMessage", summary="Telegram: отправить сообщение")
async def telegram_send(token: str, payload: Annotated[dict[str, Any], Body()]) -> dict[str, Any]:
    message = _store("telegram", str(payload.get("chat_id", "")), str(payload.get("text", "")))
    return {"ok": True, "result": {"message_id": message["id"], "chat": {"id": message["address"]}}}


@app.post("/messages", summary="Max: отправить сообщение")
async def max_send(
    access_token: Annotated[str, Query()],
    user_id: Annotated[str, Query()],
    payload: Annotated[dict[str, Any], Body()],
) -> dict[str, Any]:
    message = _store("max", user_id, str(payload.get("text", "")))
    return {"message": {"body": {"mid": str(message["id"]), "text": message["text"]}}}


@app.get("/sent", summary="Что получено")
async def sent(channel: str | None = None) -> list[dict[str, Any]]:
    return [message for message in _sent if channel is None or message["channel"] == channel]
