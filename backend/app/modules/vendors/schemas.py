import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Channel = Literal["email", "telegram", "phone"]


class VendorProductOut(BaseModel):
    id: uuid.UUID
    name: str


class VendorOut(BaseModel):
    """Вендор со своими продуктами: у справочника вендоров наконец есть id для выбора."""

    id: uuid.UUID
    name: str
    products: list[VendorProductOut]
    contacts: int = Field(description="Сколько действующих контактов у вендора")
    archived_at: datetime | None


class VendorContactOut(BaseModel):
    """Контакт вендора. Почта и телефон расшифровываются только для того, кто их запросил."""

    id: uuid.UUID
    vendor_id: uuid.UUID
    full_name: str
    email: str | None
    phone: str | None
    channels: list[Channel] = Field(description="Как удобнее связаться: почта, Telegram, звонок")
    products: list[VendorProductOut] = Field(description="За какие продукты отвечает")
    archived_at: datetime | None


class VendorContactCreate(BaseModel):
    # Строка из одних пробелов не проходит min_length: сначала обрезаем.
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=2, max_length=200)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=40)
    channels: list[Channel] = Field(default_factory=list, max_length=3)
    product_ids: list[uuid.UUID] = Field(
        default_factory=list, max_length=50, description="Продукты этого же вендора"
    )
