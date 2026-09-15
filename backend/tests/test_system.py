import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.core.config import Settings
from tests.users import ANNA_KAM, as_user


async def test_health_reports_database(client: AsyncClient) -> None:
    response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["database"] == "ok"
    assert response.headers["X-Trace-Id"]


async def test_missing_user_returns_problem_json(client: AsyncClient) -> None:
    response = await client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["code"] == "AUTH_REQUIRED"
    assert body["trace_id"] == response.headers["X-Trace-Id"]


async def test_validation_error_names_the_field(client: AsyncClient) -> None:
    response = await client.get("/api/v1/interactions?page=0", headers=as_user(ANNA_KAM))

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["errors"][0]["field"] == "page"


async def test_unknown_route_is_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/unknown", headers=as_user(ANNA_KAM))

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_dev_auth_is_forbidden_in_production() -> None:
    with pytest.raises(ValidationError, match="AUTH_MODE=dev"):
        Settings(app_env="production", auth_mode="dev")
