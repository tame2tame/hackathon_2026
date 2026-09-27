import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app import main
from app.core.config import Settings
from tests.users import ANNA_KAM, as_user


async def test_health_reports_database(client: AsyncClient) -> None:
    response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["database"] == "ok"
    assert response.json()["storage"] == "ok"
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


PRODUCTION = {
    "app_env": "production",
    "auth_mode": "keycloak",
    "database_url": "postgresql+asyncpg://radar_app:s3cret@postgres:5432/radar",
    "pd_encryption_key": "q5l2Hk3m0y8o3c1uYw7cX9m3f8d2k1r6Q0e9V4b7N2s=",
}


def test_production_settings_accept_real_secrets() -> None:
    Settings(**PRODUCTION)


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"pd_encryption_key": ""}, "требует PD_ENCRYPTION_KEY"),
        ({"pd_encryption_key": "короткий"}, "не является ключом Fernet"),
        (
            {"database_url": "postgresql+asyncpg://radar:radar@postgres:5432/radar"},
            "пароль из локального профиля",
        ),
        ({"cors_origins": "*"}, "CORS_ORIGINS"),
    ],
)
def test_production_refuses_unsafe_settings(override: dict[str, str], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        Settings(**{**PRODUCTION, **override})


async def test_frontend_on_another_address_passes_preflight(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: Settings(app_env="test", auth_mode="dev", cors_origins="https://radar.example.ru"),
    )
    app = main.create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://api") as api:
        preflight = await api.options(
            "/api/v1/interactions/x/status",
            headers={
                "Origin": "https://radar.example.ru",
                "Access-Control-Request-Method": "PUT",
                "Access-Control-Request-Headers": "last-event-id, if-none-match",
            },
        )

    assert preflight.status_code == 200
    assert "PUT" in preflight.headers["access-control-allow-methods"]
    allowed = preflight.headers["access-control-allow-headers"].lower()
    assert "last-event-id" in allowed
    assert "if-none-match" in allowed


async def test_wrong_method_has_its_own_code(client: AsyncClient) -> None:
    response = await client.put("/api/health")

    # Раньше неожиданный статус приходил с кодом VALIDATION_ERROR, и фронтенд искал ошибку в полях.
    assert response.status_code == 405
    assert response.json()["code"] == "METHOD_NOT_ALLOWED"
