"""Аутентификация: JWT Keycloak или заголовок X-Dev-User в режиме разработки (ADR-011)."""

import uuid
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Any

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings, get_settings
from app.core.db import SessionDep
from app.core.errors import AppError, ErrorCode
from app.core.roles import Role
from app.modules.catalogs.models import AppUser

DEV_USER_HEADER = "X-Dev-User"

bearer_scheme = HTTPBearer(auto_error=False, description="Access token из Keycloak")


@dataclass(frozen=True, slots=True)
class CurrentUser:
    id: uuid.UUID
    email: str
    full_name: str
    role: Role
    team_id: uuid.UUID | None
    # Правила администратора: загружаются один раз за запрос и применяются в области видимости.
    access_rules: tuple[Any, ...] = ()


@lru_cache
def _jwks_client(jwks_url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(jwks_url, lifespan=3600)


def role_from_claims(claims: dict[str, Any]) -> Role:
    roles = set(claims.get("realm_access", {}).get("roles", []))
    # При нескольких ролях действует самая широкая.
    for role in (Role.ADMIN, Role.MANAGER, Role.KAM):
        if role.value in roles:
            return role
    raise AppError(ErrorCode.AUTH_FORBIDDEN, "У учётной записи нет роли в «Радаре вузов».")


def decode_keycloak_token(token: str, settings: Settings) -> dict[str, Any]:
    """Проверяет подпись, срок, издателя и аудиторию токена. Выполняется в пуле потоков."""
    try:
        signing_key = _jwks_client(settings.jwks_url).get_signing_key_from_jwt(token)
        claims: dict[str, Any] = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.keycloak_audience,
            issuer=settings.keycloak_issuer,
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise AppError(ErrorCode.AUTH_REQUIRED, "Токен недействителен или просрочен.") from exc
    return claims


async def _user_from_claims(claims: dict[str, Any], session: AsyncSession) -> AppUser:
    role = role_from_claims(claims)
    sub = str(claims["sub"])
    email = claims.get("email")
    user = await session.scalar(select(AppUser).where(AppUser.keycloak_sub == sub))
    if user is None and email:
        # Пользователь мог быть заведён заранее по email — связываем его с учётной записью Keycloak.
        user = await session.scalar(select(AppUser).where(AppUser.email == email))
        if user is not None:
            user.keycloak_sub = sub
    if user is None:
        # При первом входе SPA шлёт несколько запросов сразу: кто первый, тот и заводит
        # сотрудника, остальные просто читают его. Иначе проигравшие получали 500.
        await session.execute(
            insert(AppUser)
            .values(
                id=uuid.uuid4(),
                keycloak_sub=sub,
                email=email or f"{sub}@users.keycloak",
                full_name=claims.get("name") or email or sub,
                role=role.value,
                is_active=True,
            )
            .on_conflict_do_nothing()
        )
        user = await session.scalar(select(AppUser).where(AppUser.keycloak_sub == sub))
        if user is None and email:
            user = await session.scalar(select(AppUser).where(AppUser.email == email))
            if user is not None and user.keycloak_sub is None:
                user.keycloak_sub = sub
        if user is None:
            raise AppError(ErrorCode.AUTH_REQUIRED, "Не удалось завести учётную запись.")
    if not user.is_active:
        # Проверяем только тех, кто уже есть в базе: у нового объекта значения по умолчанию
        # проставляются лишь при сохранении.
        raise AppError(ErrorCode.AUTH_FORBIDDEN, "Учётная запись отключена.")
    user.role = role.value  # источник правды о роли — Keycloak
    await session.commit()
    return user


async def get_current_user(
    request: Request,
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> CurrentUser:
    settings = get_settings()
    if settings.auth_mode == "dev":
        email = request.headers.get(DEV_USER_HEADER)
        if not email:
            raise AppError(ErrorCode.AUTH_REQUIRED, f"Укажите заголовок {DEV_USER_HEADER}.")
        user = await session.scalar(
            select(AppUser).where(AppUser.email == email, AppUser.is_active.is_(True))
        )
        if user is None:
            raise AppError(ErrorCode.AUTH_REQUIRED, "Пользователь не найден или отключён.")
    else:
        if credentials is None:
            raise AppError(ErrorCode.AUTH_REQUIRED, "Нужен токен доступа.")
        claims = await run_in_threadpool(decode_keycloak_token, credentials.credentials, settings)
        user = await _user_from_claims(claims, session)
    return await current_user_for(session, user)


async def current_user_for(session: AsyncSession, user: AppUser) -> CurrentUser:
    """Сотрудник вместе с его правилами доступа: одинаково для запроса и для фоновой задачи."""
    return CurrentUser(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=Role(user.role),
        team_id=user.team_id,
        access_rules=await access_rules_of(session, user),
    )


async def access_rules_of(session: AsyncSession, user: AppUser) -> tuple[Any, ...]:
    """Правила доступа сотрудника и его роли — одним запросом на весь запрос к API."""
    from app.core.scope import AccessRule
    from app.modules.admin.models import DataAccessRule

    rows = await session.scalars(
        select(DataAccessRule).where(
            or_(
                DataAccessRule.subject_user_id == user.id,
                DataAccessRule.subject_role == user.role,
            )
        )
    )
    return tuple(
        AccessRule(effect=rule.effect, scope_kind=rule.scope_kind, scope_id=rule.scope_id)
        for rule in rows
    )


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def require_roles(*roles: Role) -> Callable[..., Coroutine[Any, Any, CurrentUser]]:
    """Зависимость, пропускающая только перечисленные роли."""

    async def dependency(user: CurrentUserDep) -> CurrentUser:
        if user.role not in roles:
            raise AppError(ErrorCode.AUTH_FORBIDDEN, "Действие недоступно для вашей роли.")
        return user

    return dependency
