"""Помощники, общие для тестов API."""

import uuid
from typing import Any

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalogs.models import AppUser
from tests.users import ALINA_ADMIN, as_user


async def find(client: AsyncClient, email: str, **params: Any) -> dict[str, Any]:
    """Единственное взаимодействие, подходящее под фильтры."""
    response = await client.get("/api/v1/interactions", params=params, headers=as_user(email))
    assert response.status_code == 200
    items: list[dict[str, Any]] = response.json()["items"]
    assert len(items) == 1
    return items[0]


async def stage_id(client: AsyncClient, code: str) -> str:
    workflow = (await client.get("/api/v1/workflows/default", headers=as_user(ALINA_ADMIN))).json()
    return str(next(s["id"] for s in workflow["stages"] if s["code"] == code))


async def user_id(session: AsyncSession, email: str) -> uuid.UUID:
    found = await session.scalar(select(AppUser.id).where(AppUser.email == email))
    assert found is not None
    return found


# Минимальный настоящий PDF: важна сигнатура, содержимое роли не играет.
PDF_BYTES = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"


async def upload_pdf(
    client: AsyncClient,
    email: str,
    interaction_id: str,
    document_type: str | None = None,
    file_name: str = "Договор.pdf",
) -> dict[str, Any]:
    response = await client.post(
        f"/api/v1/interactions/{interaction_id}/attachments",
        files={"file": (file_name, PDF_BYTES, "application/pdf")},
        data={"document_type": document_type} if document_type else None,
        headers=as_user(email),
    )
    assert response.status_code == 201, response.text
    uploaded: dict[str, Any] = response.json()
    return uploaded
