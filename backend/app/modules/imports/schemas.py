"""Схемы импорта: загрузка, соответствие колонок, предпросмотр и итог применения."""

import uuid

from pydantic import BaseModel, ConfigDict, Field


class ImportProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    file_kind: str
    column_map: dict[str, str]


class RowPreview(BaseModel):
    row_no: int
    resolution: str = Field(description="new, update, conflict, skip или needs_program")
    detail: str | None = Field(description="Причина, если строка требует внимания")
    university: str
    product: str
    contract_number: str


class ImportBatchOut(BaseModel):
    id: uuid.UUID
    file_name: str
    file_kind: str = Field(description="xlsx, xls или csv")
    encoding: str | None = Field(
        description="Кодировка, в которой прочитан файл: указанная вручную или определённая"
    )
    delimiter: str | None = Field(description="Разделитель колонок CSV")
    status: str
    headers: list[str] = Field(description="Колонки файла в исходном порядке")
    column_map: dict[str, str] = Field(description="Поле модели → заголовок колонки")
    suggested_map: dict[str, str] = Field(description="Подсказка по заголовкам ТЗ")
    fields: list[str] = Field(description="Поля модели, доступные для сопоставления")
    required_fields: list[str]
    total_rows: int
    stats: dict[str, int] = Field(description="Сколько строк в каждом решении")
    rows: list[RowPreview] = Field(description="Первые строки для предпросмотра")


class MappingUpdate(BaseModel):
    column_map: dict[str, str] = Field(description="Поле модели → заголовок колонки файла")
    save_as_profile: str | None = Field(
        default=None, max_length=200, description="Сохранить соответствие под этим именем"
    )


class ApplyResult(BaseModel):
    batch_id: uuid.UUID
    created: int
    updated: int
    skipped: int
    conflicts: int
    needs_program: int
