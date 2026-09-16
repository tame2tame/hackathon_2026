"""Проверка токенов Keycloak на собственных ключах: подпись, срок, издатель, аудитория, роль."""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import Settings
from app.core.errors import AppError, ErrorCode
from app.core.roles import Role
from app.core.security import _user_from_claims, decode_keycloak_token, role_from_claims
from app.modules.catalogs.models import AppUser
from tests.users import ANNA_KAM

ISSUER = "http://keycloak.test/realms/radar-vuzov"
AUDIENCE = "radar-api"


@pytest.fixture(scope="module")
def signing_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        app_env="test",
        auth_mode="keycloak",
        keycloak_issuer=ISSUER,
        keycloak_audience=AUDIENCE,
    )


@pytest.fixture(autouse=True)
def jwks(monkeypatch: pytest.MonkeyPatch, signing_key: rsa.RSAPrivateKey) -> None:
    """Вместо похода в Keycloak за ключами подставляем открытый ключ тестовой пары."""

    class FakeSigningKey:
        def __init__(self, key: object) -> None:
            self.key = key

    class FakeClient:
        def __init__(self, key: object) -> None:
            self._key = FakeSigningKey(key)

        def get_signing_key_from_jwt(self, token: str) -> FakeSigningKey:
            return self._key

    monkeypatch.setattr(security, "_jwks_client", lambda url: FakeClient(signing_key.public_key()))


def make_token(key: rsa.RSAPrivateKey, **overrides: Any) -> str:
    now = datetime.now(UTC)
    claims: dict[str, Any] = {
        "sub": "6f1a3c4e-0000-4000-8000-000000000001",
        "email": ANNA_KAM,
        "name": "Анна Смирнова",
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "realm_access": {"roles": ["kam"]},
    }
    claims.update(overrides)
    return jwt.encode(claims, key, algorithm="RS256")


def test_valid_token_is_accepted(signing_key: rsa.RSAPrivateKey, settings: Settings) -> None:
    claims = decode_keycloak_token(make_token(signing_key), settings)

    assert claims["email"] == ANNA_KAM
    assert claims["realm_access"]["roles"] == ["kam"]


def test_expired_token_is_rejected(signing_key: rsa.RSAPrivateKey, settings: Settings) -> None:
    now = datetime.now(UTC)
    token = make_token(signing_key, iat=now - timedelta(hours=2), exp=now - timedelta(hours=1))

    with pytest.raises(AppError) as error:
        decode_keycloak_token(token, settings)
    assert error.value.code is ErrorCode.AUTH_REQUIRED


@pytest.mark.parametrize(
    ("claim", "value"),
    [("aud", "other-api"), ("iss", "http://evil.test/realms/radar-vuzov")],
)
def test_foreign_audience_or_issuer_is_rejected(
    signing_key: rsa.RSAPrivateKey, settings: Settings, claim: str, value: str
) -> None:
    with pytest.raises(AppError) as error:
        decode_keycloak_token(make_token(signing_key, **{claim: value}), settings)
    assert error.value.code is ErrorCode.AUTH_REQUIRED


def test_token_signed_by_another_key_is_rejected(settings: Settings) -> None:
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    with pytest.raises(AppError) as error:
        decode_keycloak_token(make_token(other), settings)
    assert error.value.code is ErrorCode.AUTH_REQUIRED


def test_broadest_role_wins() -> None:
    assert role_from_claims({"realm_access": {"roles": ["kam", "manager"]}}) is Role.MANAGER

    with pytest.raises(AppError) as error:
        role_from_claims({"realm_access": {"roles": ["offline_access"]}})
    assert error.value.code is ErrorCode.AUTH_FORBIDDEN


async def test_existing_user_is_linked_by_email(session: AsyncSession) -> None:
    claims = {
        "sub": "kc-sub-anna",
        "email": ANNA_KAM,
        "realm_access": {"roles": ["kam"]},
    }

    user = await _user_from_claims(claims, session)

    assert user.email == ANNA_KAM
    assert user.keycloak_sub == "kc-sub-anna"
    assert user.team_id is not None  # команда из БД, а не из токена


async def test_unknown_user_is_created_with_role_from_token(session: AsyncSession) -> None:
    claims = {
        "sub": "kc-sub-new",
        "email": "new.manager@example.com",
        "name": "Новый Руководитель",
        "realm_access": {"roles": ["manager"]},
    }

    user = await _user_from_claims(claims, session)

    stored = await session.scalar(select(AppUser).where(AppUser.keycloak_sub == "kc-sub-new"))
    assert stored is not None
    assert (stored.id, stored.role, stored.full_name) == (user.id, "manager", "Новый Руководитель")
