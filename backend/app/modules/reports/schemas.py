"""Схемы отчётов: параметры задания и его состояние."""

import uuid
from datetime import date, datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Колонка → заголовок в файле. Порядок здесь задаёт порядок колонок по умолчанию.
COLUMNS: dict[str, str] = {
    "group": "Группа",
    "counterparty": "Контрагент",
    "university": "Вуз",
    "direction": "Направление",
    "program": "Программа",
    "product": "Продукт",
    "stage": "Этап на конец периода",
    "owner": "Ответственный",
    "contract": "Договор",
    "license_valid_until": "Срок лицензии",
    "days_on_stage": "Дней на этапе",
    "signals": "Сигналы",
}
DEFAULT_COLUMNS = tuple(COLUMNS)
ReportFormat = Literal["xlsx", "xls", "csv", "pdf", "json"]


class ReportCreate(BaseModel):
    """Те же фильтры, что у списка взаимодействий, плюс колонки и формат файла."""

    format: ReportFormat = "xlsx"
    encoding: Literal["utf-8", "windows-1251"] = Field(
        default="utf-8",
        description="Кодировка CSV: utf-8 (с BOM, без потерь) или windows-1251 для старых программ",
    )
    period_from: date | None = None
    period_to: date | None = None
    group_id: list[uuid.UUID] = Field(default_factory=list)
    university_id: list[uuid.UUID] = Field(default_factory=list)
    direction_id: list[uuid.UUID] = Field(default_factory=list)
    program_id: list[uuid.UUID] = Field(default_factory=list)
    product_id: list[uuid.UUID] = Field(default_factory=list)
    owner_id: list[uuid.UUID] = Field(default_factory=list)
    stage_code: list[str] = Field(default_factory=list)
    status: list[Literal["active", "paused", "completed", "cancelled"]] = Field(
        default_factory=list, description="Состояние записи; без фильтра отменённые не попадают"
    )
    search: str | None = Field(default=None, max_length=100)
    columns: list[str] = Field(
        default_factory=lambda: list(DEFAULT_COLUMNS),
        min_length=1,
        description=f"Из набора: {', '.join(COLUMNS)}",
    )

    @model_validator(mode="after")
    def check_columns(self) -> Self:
        unknown = [column for column in self.columns if column not in COLUMNS]
        if unknown:
            raise ValueError(f"Неизвестные колонки: {', '.join(unknown)}")
        return self


class ReportJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str = Field(description="queued, running, done или failed")
    progress: int = Field(description="Процент готовности")
    format: str
    row_count: int | None
    error_code: str | None = Field(description="Код ошибки из каталога, если отчёт не построен")
    created_at: datetime
    finished_at: datetime | None
