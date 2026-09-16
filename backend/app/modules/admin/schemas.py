"""Схемы администрирования: пользователи, команды, правила доступа, настройки, аудит."""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.roles import Role

Effect = Literal["allow", "deny"]
ScopeKind = Literal["university", "direction", "program"]


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: Role
    team_id: uuid.UUID | None
    is_active: bool


class AdminUserUpdate(BaseModel):
    role: Role | None = None
    team_id: uuid.UUID | None = None
    is_active: bool | None = Field(default=None, description="Отключённый сотрудник не входит")


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    manager_user_id: uuid.UUID | None


class TeamCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    manager_user_id: uuid.UUID | None = None


class AccessRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subject_user_id: uuid.UUID | None
    subject_role: str | None
    effect: str
    scope_kind: str
    scope_id: uuid.UUID
    comment: str | None


class AccessRuleCreate(BaseModel):
    """Правило адресуется либо сотруднику, либо роли — ровно одно из двух."""

    subject_user_id: uuid.UUID | None = None
    subject_role: Role | None = None
    effect: Effect
    scope_kind: ScopeKind
    scope_id: uuid.UUID
    comment: str | None = Field(default=None, max_length=500)


class SettingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    value: dict[str, Any]
    updated_at: datetime


class SettingUpdate(BaseModel):
    value: dict[str, Any]


class AuditEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    occurred_at: datetime
    actor_user_id: uuid.UUID | None
    action: str
    entity_kind: str
    entity_id: uuid.UUID | None
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    trace_id: str | None


class ContactOut(BaseModel):
    """Контакт вуза. Email и телефон расшифровываются только для того, кто их запросил."""

    id: uuid.UUID
    university_id: uuid.UUID
    full_name: str
    position: str | None
    email: str | None
    phone: str | None
    archived_at: datetime | None


class ContactCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    position: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=40)


class CatalogItemCreate(BaseModel):
    name: str = Field(min_length=2, max_length=300)
    code: str | None = Field(default=None, max_length=60, description="Только для направлений")
    short_name: str | None = Field(default=None, max_length=60, description="Только для вузов")
    region: str | None = Field(default=None, max_length=120, description="Только для вузов")
    city: str | None = Field(default=None, max_length=120)
    direction_id: uuid.UUID | None = Field(default=None, description="Только для программ")
    vendor_id: uuid.UUID | None = Field(default=None, description="Только для продуктов")


class CatalogItemOut(BaseModel):
    id: uuid.UUID
    name: str
    archived_at: datetime | None
