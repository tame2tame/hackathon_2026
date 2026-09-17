"""Схемы каталогов и краткие ссылки на сущности для вложения в другие ответы."""

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.roles import Role
from app.core.scope import ScopeName


class _FromAttributes(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class GroupRef(_FromAttributes):
    id: uuid.UUID
    code: str
    name: str


class CounterpartyGroupOut(GroupRef):
    description: str | None
    workflow_template_id: uuid.UUID = Field(description="Процесс, по которому идут записи группы")
    position: int


class CounterpartyRef(_FromAttributes):
    """Контрагент записи: вуз, человек или организация — одной ссылкой для списков."""

    kind: Literal["university", "person", "organization"]
    id: uuid.UUID
    name: str
    short_name: str = Field(description="Сокращение вуза; у клиента совпадает с именем")


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
