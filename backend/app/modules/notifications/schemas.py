"""Схемы уведомлений: лента сотрудника, адреса в каналах, настройки каналов и журнал доставки."""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

NotificationKind = Literal[
    "stalled_interaction", "stage_changed", "workflow_changed", "channel_test"
]
ChannelKind = Literal["telegram", "max", "email"]


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: NotificationKind
    title: str
    body: str
    interaction_id: uuid.UUID | None
    payload: dict[str, Any]
    created_at: datetime
    read_at: datetime | None


class ReadAllOut(BaseModel):
    updated: int = Field(description="Сколько уведомлений отмечено прочитанными")


class AddressOut(BaseModel):
    channel_kind: ChannelKind
    channel_name: str
    channel_enabled: bool = Field(description="Включил ли канал администратор")
    address: str | None = Field(description="Чат Telegram, пользователь Max или email")
    is_enabled: bool


class AddressUpdate(BaseModel):
    # Строка из одних пробелов не проходит min_length: сначала обрезаем.
    model_config = ConfigDict(str_strip_whitespace=True)

    address: str = Field(min_length=1, max_length=254)
    is_enabled: bool = True


class ChannelOut(BaseModel):
    kind: ChannelKind
    name: str
    is_enabled: bool
    is_mock: bool = Field(description="Канал смотрит в заглушку, а не в настоящий сервис")
    settings: dict[str, Any] = Field(description="Адрес API или почтового сервера, без секретов")
    secret_ref: str | None = Field(description="Имя переменной окружения с токеном или паролем")
    secret_configured: bool = Field(description="Переменная с секретом задана на сервере")
    kinds: list[NotificationKind] = Field(description="Какие уведомления канал пересылает")
    updated_at: datetime


class ChannelUpdate(BaseModel):
    """Пропущенное поле не меняется. Секрет задаётся именем переменной окружения `NOTIFY_*`."""

    is_enabled: bool | None = None
    is_mock: bool | None = None
    settings: dict[str, Any] | None = None
    secret_ref: str | None = Field(default=None, pattern=r"^NOTIFY_[A-Z0-9_]{1,60}$")
    kinds: list[NotificationKind] | None = None


class DeliveryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    notification_id: uuid.UUID
    channel_kind: ChannelKind
    status: Literal["pending", "sent", "failed"]
    attempts: int
    last_error: str | None
    next_attempt_at: datetime
    sent_at: datetime | None
    created_at: datetime


class EscalationRunOut(BaseModel):
    notified: int = Field(description="Сколько уведомлений о зависших записях создано")
