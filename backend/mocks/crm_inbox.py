"""Приём документов CRM, общий для заглушек LMS и сайта: `POST` и `GET /api/crm/interactions`.

Заглушка хранит последнюю версию каждой записи и отклоняет документы незнакомого формата —
так видно и успешную отправку, и отказ получателя по содержанию.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Body

FORMAT = "radar-vuzov/interaction@1"


def crm_inbox() -> APIRouter:
    router = APIRouter(prefix="/api/crm", tags=["crm"])
    received: dict[str, dict[str, Any]] = {}

    @router.post("/interactions", summary="Принять изменения записей CRM")
    async def receive(payload: Annotated[dict[str, Any], Body()]) -> dict[str, Any]:
        accepted: list[str] = []
        rejected: list[dict[str, str]] = []
        for item in payload.get("items", []):
            record: dict[str, Any] = item.get("record") or {} if isinstance(item, dict) else {}
            key = str(record.get("id", ""))
            if not key or item.get("format") != FORMAT:
                rejected.append({"id": key, "reason": "Незнакомый формат документа"})
                continue
            stored = received.get(key)
            # Устаревшая версия не затирает новую: документы могут прийти не по порядку.
            if stored is None or stored["record"]["version"] <= int(record.get("version", 0)):
                received[key] = item
            accepted.append(key)
        return {"accepted": accepted, "rejected": rejected}

    @router.get("/interactions", summary="Что получено от CRM")
    async def listing() -> list[dict[str, Any]]:
        return list(received.values())

    return router
