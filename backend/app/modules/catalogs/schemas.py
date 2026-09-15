"""Схемы каталогов и краткие ссылки на сущности для вложения в другие ответы."""

import uuid

from pydantic import BaseModel, ConfigDict

from app.core.roles import Role
from app.core.scope import ScopeName


class _FromAttributes(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UniversityRef(_FromAttributes):
    id: uuid.UUID
    name: str
    short_name: str
    region: str


class DirectionRef(_FromAttributes):
    id: uuid.UUID
    code: str
    name: str


class ProgramRef(_FromAttributes):
    id: uuid.UUID
    name: str
    direction: DirectionRef


class VendorRef(_FromAttributes):
    id: uuid.UUID
    name: str


class ProductRef(_FromAttributes):
    id: uuid.UUID
    name: str
    vendor: VendorRef


class UserRef(_FromAttributes):
    id: uuid.UUID
    full_name: str


class TeamRef(_FromAttributes):
    id: uuid.UUID
    name: str


class UserOut(UserRef):
    email: str
    role: Role


class MeOut(UserOut):
    team: TeamRef | None
    scope: ScopeName


class UniversityOut(UniversityRef):
    city: str | None
    interactions_count: int
    open_signals_count: int
