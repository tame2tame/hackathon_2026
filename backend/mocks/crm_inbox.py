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
        items = payload.get("items")
        for item in items if isinstance(items, list) else []:
            # Мусор в пакете — отказ по этому документу, а не 500 на весь пакет.
            record = item.get("record") if isinstance(item, dict) else None
            key = str(record.get("id", "")) if isinstance(record, dict) else ""
            version = record.get("version") if isinstance(record, dict) else None
            if not key or item.get("format") != FORMAT or not isinstance(version, int):
                rejected.append({"id": key, "reason": "Незнакомый формат документа"})
                continue
            stored = received.get(key)
            # Устаревшая версия не затирает новую: документы могут прийти не по порядку.
            if stored is None or stored["record"]["version"] <= version:
                received[key] = item
            accepted.append(key)
        return {"accepted": accepted, "rejected": rejected}

    @router.get("/interactions", summary="Что получено от CRM")
    async def listing() -> list[dict[str, Any]]:
        return list(received.values())

    return router
