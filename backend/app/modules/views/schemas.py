"""Схемы сохранённых видов."""

import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

ViewPage = Literal["interactions", "radar", "reports", "rating", "clients"]
MAX_FILTERS_BYTES = 4096
# Колонка — это имя поля, а не текст: длинная строка здесь означает, что видом пытаются
# что-то хранить.
Column = Annotated[str, StringConstraints(min_length=1, max_length=60)]


class SavedViewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    page: ViewPage
    name: str
    filters: dict[str, Any]
    columns: list[str]
    updated_at: datetime


class SavedViewCreate(BaseModel):
    # Строка из одних пробелов не проходит min_length: сначала обрезаем.
    model_config = ConfigDict(str_strip_whitespace=True)

    page: ViewPage
    name: str = Field(min_length=1, max_length=100)
    filters: dict[str, Any] = Field(
        default_factory=dict, description="Параметры запроса страницы: сервер их не толкует"
    )
    columns: list[Column] = Field(
        default_factory=list, max_length=40, description="Колонки списка в нужном порядке"
    )


class SavedViewUpdate(BaseModel):
    # Строка из одних пробелов не проходит min_length: сначала обрезаем.
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=100)
    filters: dict[str, Any] | None = None
    columns: list[Column] | None = Field(default=None, max_length=40)
