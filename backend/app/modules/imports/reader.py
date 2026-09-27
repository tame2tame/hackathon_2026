"""Чтение выгрузок: xlsx через openpyxl, xls через xlrd, csv — с определением кодировки.

Значения приводятся к строкам. Кодировка — самое частое место, где файл «слетает»: выгрузка из
1С или старого Excel приходит в cp1251, из почтовых систем — в KOI8-R, из консольных утилит —
в cp866. Поэтому кодировку можно задать вручную, а без неё она определяется по содержимому.
"""

import csv
import io
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import openpyxl
import xlrd

MAX_ROWS = 5000
DATE_FORMATS = ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d", "%d/%m/%Y")
FILE_KINDS = {".xls": "xls", ".xlsx": "xlsx", ".csv": "csv"}

# Кодировка из интерфейса → имя кодека Python. Порядок задаёт выбор при равной оценке.
ENCODINGS = {
    "utf-8": "utf-8",
    "windows-1251": "cp1251",
    "koi8-r": "koi8_r",
    "cp866": "cp866",
    "utf-16": "utf-16",
}
CYRILLIC_CANDIDATES = ("windows-1251", "koi8-r", "cp866")
LOWER = frozenset("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
UPPER = frozenset("АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ")
DELIMITERS = ";,\t|"


@dataclass(frozen=True, slots=True)
class Sheet:
    headers: list[str]
    rows: list[dict[str, str]]
    encoding: str | None = None
    delimiter: str | None = None


class SheetError(Exception):
    """Файл не удалось разобрать: не тот формат, кодировка или нет строки заголовков."""


def file_kind(file_name: str) -> str | None:
    return FILE_KINDS.get(Path(file_name).suffix.lower())


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


def _sheet_from_rows(
    raw_rows: list[list[str]], encoding: str | None = None, delimiter: str | None = None
) -> Sheet:
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
        if len(rows) >= MAX_ROWS:
            # Молча обрезать нельзя: пользователь решил бы, что загрузил весь файл.
            raise SheetError(
                f"В файле больше {MAX_ROWS} строк. Разбейте его на части и загрузите по очереди."
            )
        rows.append({header: value for header, value in zip(headers, raw, strict=False) if header})
    if not headers:
        raise SheetError("В файле не нашлась строка заголовков.")
    return Sheet(
        headers=[header for header in headers if header],
        rows=rows,
        encoding=encoding,
        delimiter=delimiter,
    )


def _read_xlsx(content: bytes) -> list[list[str]]:
    workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    try:
        worksheet = workbook.worksheets[0]
        return [[_cell(cell) for cell in row] for row in worksheet.iter_rows(values_only=True)]
    finally:
        workbook.close()


def _read_xls(content: bytes, encoding: str | None) -> list[list[str]]:
    # Кодировка нужна только старым книгам Excel 95 без кодовой страницы; в xls 97 и новее
    # строки хранятся в Юникоде, и подсказка ни на что не влияет.
    book = xlrd.open_workbook(
        file_contents=content, encoding_override=ENCODINGS[encoding] if encoding else None
    )
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


def _cyrillic_score(text: str) -> int:
    """Русский текст в верной кодировке — в основном строчные буквы; в чужой — заглавные и мусор."""
    lower = sum(1 for char in text if char in LOWER)
    upper = sum(1 for char in text if char in UPPER)
    return lower - upper


def detect_encoding(content: bytes) -> str:
    """Кодировка текста: по BOM, по строгому UTF-8, иначе лучшая из кириллических однобайтовых."""
    if content.startswith(b"\xef\xbb\xbf"):
        return "utf-8"
    if content.startswith((b"\xff\xfe", b"\xfe\xff")):
        return "utf-16"
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        pass
    else:
        return "utf-8"
    best, best_score = "windows-1251", None
    sample = content[:65536]
    for name in CYRILLIC_CANDIDATES:
        try:
            text = sample.decode(ENCODINGS[name])
        except UnicodeDecodeError:
            continue
        score = _cyrillic_score(text)
        if best_score is None or score > best_score:
            best, best_score = name, score
    return best


def _decode(content: bytes, encoding: str) -> str:
    codec = ENCODINGS[encoding]
    if encoding == "utf-8":
        codec = "utf-8-sig"  # BOM не должен попасть в первый заголовок
    try:
        return content.decode(codec)
    except UnicodeDecodeError as error:
        raise SheetError(
            f"Файл не читается в кодировке {encoding}: выберите другую кодировку."
        ) from error


def _delimiter(text: str) -> str:
    lines = [line for line in text.splitlines()[:20] if line.strip()]
    sample = "\n".join(lines)
    try:
        return csv.Sniffer().sniff(sample, delimiters=DELIMITERS).delimiter
    except csv.Error:
        # Excel в русской локали сохраняет CSV через точку с запятой.
        first = lines[0] if lines else ""
        return max(DELIMITERS, key=lambda candidate: (first.count(candidate), candidate == ";"))


def _read_csv(content: bytes, encoding: str | None) -> tuple[list[list[str]], str, str]:
    if b"\x00" in content[:4096] and not content.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise SheetError("Это не текстовый файл CSV.")
    chosen = encoding or detect_encoding(content)
    text = _decode(content, chosen)
    lines = text.splitlines(keepends=True)
    # Строка «sep=;» — указание Excel о разделителе, а не данные.
    if lines and lines[0].strip().lower().startswith("sep=") and len(lines[0].strip()) == 5:
        delimiter = lines[0].strip()[4]
        text = "".join(lines[1:])
    else:
        delimiter = _delimiter(text)
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)
    rows = [[_cell(value) for value in row] for row in reader]
    return rows, chosen, delimiter


def read(file_name: str, content: bytes, encoding: str | None = None) -> Sheet:
    kind = file_kind(file_name)
    if kind is None:
        raise SheetError("Поддерживаются файлы xls, xlsx и csv.")
    if encoding is not None and encoding not in ENCODINGS:
        raise SheetError(f"Неизвестная кодировка: {encoding}.")
    try:
        if kind == "csv":
            raw_rows, detected, delimiter = _read_csv(content, encoding)
            return _sheet_from_rows(raw_rows, detected, delimiter)
        raw_rows = _read_xlsx(content) if kind == "xlsx" else _read_xls(content, encoding)
    except SheetError:
        raise
    except Exception as error:  # любая ошибка разбора выглядит для клиента одинаково
        raise SheetError("Файл не удалось прочитать: проверьте формат и кодировку.") from error
    return _sheet_from_rows(raw_rows, encoding if kind == "xls" else None)


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
