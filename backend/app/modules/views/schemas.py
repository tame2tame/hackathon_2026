"""Схемы сохранённых видов."""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ViewPage = Literal["interactions", "radar", "reports", "rating", "clients"]
MAX_FILTERS_BYTES = 4096


class SavedViewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    page: ViewPage
    name: str
    filters: dict[str, Any]
    columns: list[str]
    updated_at: datetime


class SavedViewCreate(BaseModel):
    page: ViewPage
    name: str = Field(min_length=1, max_length=100)
    filters: dict[str, Any] = Field(
        default_factory=dict, description="Параметры запроса страницы: сервер их не толкует"
    )
    columns: list[str] = Field(
        default_factory=list, max_length=40, description="Колонки списка в нужном порядке"
    )


class SavedViewUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    filters: dict[str, Any] | None = None
    columns: list[str] | None = Field(default=None, max_length=40)
