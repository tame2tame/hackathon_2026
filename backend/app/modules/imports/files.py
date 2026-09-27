"""Общее для загрузок файлом: разбор JSON и таблиц, колонки по заголовку, итог по строкам.

Этим кодом пользуются и справочники в админке, и списки обучающихся: файл заказчика приходит
в JSON, CSV, XLSX или XLS, колонки называются по-русски, а итог показывается построчно —
чтобы одна кривая строка не отменяла весь файл.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Literal

from app.core.errors import AppError, ErrorCode, FieldError
from app.modules.imports import reader
from app.modules.imports.mapping import normalize

Action = Literal["created", "updated", "unchanged", "error"]
EXPORT_TYPES = {
    "json": "application/json",
    "csv": "text/csv",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


@dataclass(frozen=True, slots=True)
class FieldSpec:
    name: str
    label: str
    required: bool = False
    is_bool: bool = False
    aliases: tuple[str, ...] = ()

    def matches(self, header: str) -> bool:
        key = normalize(header)
        return key in {normalize(self.name), normalize(self.label), *map(normalize, self.aliases)}


@dataclass(slots=True)
class RowResult:
    row_no: int
    key: str
    action: Action
    detail: str | None = None


@dataclass(slots=True)
class ImportOutcome:
    kind: str
    dry_run: bool
    rows: list[RowResult] = field(default_factory=list)

    def count(self, action: Action) -> int:
        return sum(1 for row in self.rows if row.action == action)


class RowError(Exception):
    """Строку нельзя применить: причина уходит в итог по строке, остальные строки не страдают."""


def clean(value: Any) -> str:
    text = "" if value is None else str(value).strip()
    # Апостроф перед формулой ставит наша же выгрузка: при загрузке он лишний.
    if text.startswith("'") and text[1:2] in {"=", "+", "-", "@"}:
        return text[1:]
    return text


def parse_json(content: bytes) -> list[dict[str, Any]]:
    try:
        data = json.loads(content.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError) as error:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Файл JSON не разобран: нужен массив объектов или объект с полем items.",
            errors=[FieldError(field="file", message="Некорректный JSON")],
        ) from error
    items = data.get("items") if isinstance(data, dict) else data
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "В JSON нужен массив объектов или объект с полем items.",
            errors=[FieldError(field="file", message="Нет списка записей")],
        )
    if len(items) > reader.MAX_ROWS:
        # Тот же предел, что у таблиц: каждая строка — отдельная точка сохранения в одном запросе.
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            f"В файле больше {reader.MAX_ROWS} записей. Разбейте его на части.",
            errors=[FieldError(field="file", message="Слишком много записей")],
        )
    return items


def records(
    file_name: str, content: bytes, encoding: str | None, what: str
) -> list[dict[str, Any]]:
    """Строки файла как словари «заголовок → значение»; `what` попадает в текст ошибки."""
    if file_name.lower().endswith(".json"):
        return parse_json(content)
    if reader.file_kind(file_name) is None:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            f"{what} загружается из JSON, CSV, XLSX или XLS.",
            errors=[FieldError(field="file", message="Неподдерживаемый формат")],
        )
    try:
        sheet = reader.read(file_name, content, encoding)
    except reader.SheetError as error:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            str(error),
            errors=[FieldError(field="file", message="Файл не разобран")],
        ) from error
    return list(sheet.rows)


def normalized(specs: tuple[FieldSpec, ...], raw: dict[str, Any]) -> dict[str, str]:
    """Колонки файла → поля: подходят и имена полей, и русские заголовки."""
    values: dict[str, str] = {}
    for spec in specs:
        for header, value in raw.items():
            if spec.matches(str(header)):
                values[spec.name] = clean(value)
                break
    return values


def check_columns(specs: tuple[FieldSpec, ...], rows: list[dict[str, Any]]) -> None:
    headers = {str(header) for record in rows for header in record}
    missing = [
        spec
        for spec in specs
        if spec.required and not any(spec.matches(header) for header in headers)
    ]
    if rows and missing:
        raise AppError(
            ErrorCode.IMPORT_MAPPING_INVALID,
            f"Нет обязательных колонок: {', '.join(spec.label for spec in missing)}.",
            errors=[
                FieldError(field=spec.name, message=f"Нужна колонка «{spec.label}»")
                for spec in missing
            ],
        )
