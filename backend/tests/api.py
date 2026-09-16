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
