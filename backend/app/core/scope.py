"""Область видимости данных (ARCHITECTURE.md, раздел 4).

Любой запрос к взаимодействиям и связанным с ними данным проходит через эти функции.
"""

from typing import Any, Literal

from sqlalchemy import Select, or_, select

from app.core.roles import Role
from app.core.security import CurrentUser
from app.modules.catalogs.models import AppUser
from app.modules.interactions.models import Interaction

ScopeName = Literal["own", "team", "all"]


def scope_name(user: CurrentUser) -> ScopeName:
    if user.role is Role.ADMIN:
        return "all"
    if user.role is Role.MANAGER and user.team_id is not None:
        return "team"
    return "own"


def apply_interaction_scope[S: Select[Any]](stmt: S, user: CurrentUser) -> S:
    """Ограничивает выборку взаимодействиями, которые пользователь вправе видеть."""
    match scope_name(user):
        case "all":
            return stmt
        case "team":
            team_members = select(AppUser.id).where(AppUser.team_id == user.team_id)
            return stmt.where(
                or_(
                    Interaction.owner_user_id == user.id,
                    Interaction.owner_user_id.in_(team_members),
                )
            )
        case "own":
            return stmt.where(Interaction.owner_user_id == user.id)
