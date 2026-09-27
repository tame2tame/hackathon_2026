"""Схемы переписки внутри сервиса."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.catalogs.schemas import UserRef


class MessageInteractionRef(BaseModel):
    """Запись, о которой речь. Показывается только тому, кому она доступна."""

    id: uuid.UUID
    label: str


class MessageOut(BaseModel):
    id: uuid.UUID
    sender: UserRef
    recipient: UserRef
    body: str
    interaction: MessageInteractionRef | None = Field(
        default=None, description="Запись, о которой сообщение, если она доступна читателю"
    )
    created_at: datetime
    read_at: datetime | None


class MessageCreate(BaseModel):
    # Строка из одних пробелов не проходит min_length: сначала обрезаем.
    model_config = ConfigDict(str_strip_whitespace=True)

    recipient_id: uuid.UUID
    body: str = Field(min_length=1, max_length=2000)
    interaction_id: uuid.UUID | None = Field(
        default=None, description="Запись, о которой сообщение"
    )


class DialogOut(BaseModel):
    peer: UserRef
    last_message: str = Field(description="Начало последнего сообщения в переписке")
    last_at: datetime
    unread: int = Field(description="Сколько его сообщений вы ещё не читали")


class DialogsOut(BaseModel):
    unread_total: int
    items: list[DialogOut]


class ReadOut(BaseModel):
    updated: int
