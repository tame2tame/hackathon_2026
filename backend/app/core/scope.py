"""Область видимости данных (ARCHITECTURE.md, раздел 4).

Любой запрос к взаимодействиям и связанным с ними данным проходит через эти функции.
"""

import uuid
from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy import ColumnElement, Select, and_, not_, or_, select

from app.core.roles import Role
from app.core.security import CurrentUser
from app.modules.catalogs.models import AppUser, Program
from app.modules.interactions.models import Interaction

ScopeName = Literal["own", "team", "all"]


@dataclass(frozen=True, slots=True)
class AccessRule:
    """Правило администратора поверх ролей: запрет сильнее разрешения."""

    effect: str
    scope_kind: str
    scope_id: uuid.UUID


def _rule_condition(rule: AccessRule) -> ColumnElement[bool]:
    match rule.scope_kind:
        case "university":
            return Interaction.university_id == rule.scope_id
        case "program":
            return Interaction.program_id == rule.scope_id
        case _:
            return Interaction.program_id.in_(
                select(Program.id).where(Program.direction_id == rule.scope_id)
            )


def scope_name(user: CurrentUser) -> ScopeName:
    if user.role is Role.ADMIN:
        return "all"
    if user.role is Role.MANAGER and user.team_id is not None:
        return "team"
    return "own"


def apply_interaction_scope[S: Select[Any]](stmt: S, user: CurrentUser) -> S:
    """Ограничивает выборку взаимодействиями, которые пользователь вправе видеть.

    Сначала работает роль, затем правила администратора: разрешения расширяют область,
    запреты вычитают из неё и сильнее любого разрешения.
    """
    by_role: ColumnElement[bool] | None = None
    match scope_name(user):
        case "all":
            by_role = None
        case "team":
            team_members = select(AppUser.id).where(AppUser.team_id == user.team_id)
            by_role = or_(
                Interaction.owner_user_id == user.id,
                Interaction.owner_user_id.in_(team_members),
            )
        case "own":
            by_role = Interaction.owner_user_id == user.id

    allows = [_rule_condition(rule) for rule in user.access_rules if rule.effect == "allow"]
    denies = [_rule_condition(rule) for rule in user.access_rules if rule.effect == "deny"]

    visible = by_role
    if allows:
        visible = or_(*allows) if visible is None else or_(visible, *allows)
    if denies:
        forbidden = not_(or_(*denies))
        visible = forbidden if visible is None else and_(visible, forbidden)
    return stmt if visible is None else stmt.where(visible)
