"""Чтение выгрузок: xlsx через openpyxl, xls через xlrd. Значения приводятся к строкам."""

import io
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import openpyxl
import xlrd

MAX_ROWS = 5000
DATE_FORMATS = ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d", "%d/%m/%Y")


@dataclass(frozen=True, slots=True)
class Sheet:
    headers: list[str]
    rows: list[dict[str, str]]


class SheetError(Exception):
    """Файл не удалось разобрать: не тот формат или нет строки заголовков."""


def file_kind(file_name: str) -> str | None:
    suffix = Path(file_name).suffix.lower()
    return suffix[1:] if suffix in {".xls", ".xlsx"} else None


def _cell(value: Any) -> str:
    """Любая ячейка становится строкой; дата — в привычном «дд.мм.гггг»."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.date().strftime("%d.%m.%Y")
    if isinstance(value, date):
        return value.strftime("%d.%m.%Y")
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _sheet_from_rows(raw_rows: list[list[str]]) -> Sheet:
    headers: list[str] = []
    rows: list[dict[str, str]] = []
    for raw in raw_rows:
        if not headers:
            # Первая строка хотя бы с двумя заполненными ячейками — это заголовки.
            if sum(1 for cell in raw if cell) >= 2:
                headers = [cell for cell in raw]
            continue
        if not any(raw):
            continue
        rows.append({header: value for header, value in zip(headers, raw, strict=False) if header})
        if len(rows) >= MAX_ROWS:
            break
    if not headers:
        raise SheetError("В файле не нашлась строка заголовков.")
    return Sheet(headers=[header for header in headers if header], rows=rows)


def _read_xlsx(content: bytes) -> list[list[str]]:
    workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    try:
        worksheet = workbook.worksheets[0]
        return [[_cell(cell) for cell in row] for row in worksheet.iter_rows(values_only=True)]
    finally:
        workbook.close()


def _read_xls(content: bytes) -> list[list[str]]:
    book = xlrd.open_workbook(file_contents=content)
    try:
        sheet = book.sheet_by_index(0)
        rows: list[list[str]] = []
        for row_no in range(sheet.nrows):
            values: list[str] = []
            for cell in sheet.row(row_no):
                if cell.ctype == xlrd.XL_CELL_DATE:
                    values.append(_cell(xlrd.xldate_as_datetime(cell.value, book.datemode)))
                else:
                    values.append(_cell(cell.value))
            rows.append(values)
        return rows
    finally:
        book.release_resources()


def read(file_name: str, content: bytes) -> Sheet:
    kind = file_kind(file_name)
    if kind is None:
        raise SheetError("Поддерживаются только файлы xls и xlsx.")
    try:
        raw_rows = _read_xlsx(content) if kind == "xlsx" else _read_xls(content)
    except SheetError:
        raise
    except Exception as error:  # любая ошибка разбора выглядит для клиента одинаково
        raise SheetError("Файл не удалось прочитать: проверьте, что это книга Excel.") from error
    return _sheet_from_rows(raw_rows)


def parse_date(value: str | None) -> date | None:
    text = (value or "").strip()
    if not text:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None
