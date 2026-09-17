"""Схемы клиентов: физических и юридических лиц вне вузов."""

import uuid
from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

ClientKind = Literal["person", "organization"]


class ClientRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: ClientKind
    name: str = Field(description="ФИО человека или наименование организации")


class ClientListItem(ClientRef):
    inn: str | None
    city: str | None


class ClientOut(ClientListItem):
    """Карточка клиента. Email и телефон расшифровываются только по запросу карточки."""

    email: str | None
    phone: str | None
    archived_at: datetime | None


class ClientCreate(BaseModel):
    kind: ClientKind
    name: str = Field(min_length=2, max_length=300)
    inn: str | None = Field(
        default=None, pattern=r"^\d{10}$|^\d{12}$", description="ИНН организации: 10 или 12 цифр"
    )
    city: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=40)

    @model_validator(mode="after")
    def inn_only_for_organizations(self) -> Self:
        # ИНН человека — лишние персональные данные: для обучения он не нужен.
        if self.kind == "person" and self.inn:
            raise ValueError("ИНН указывается только у организации")
        return self
