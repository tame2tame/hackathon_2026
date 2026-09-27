"""Кодировки: CSV в любой из распространённых кодировок на входе и отчёты, читаемые обратно."""

import io
import json
from datetime import date
from typing import Any

import openpyxl
import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalogs.models import University
from app.modules.imports.reader import SheetError, detect_encoding, read
from scripts.make_import_fixture import HEADERS, build_csv, build_workbook
from tests.users import ANNA_KAM, ROMAN_MANAGER, as_user

EXPORT = (
    "Название ВУЗа;Вендор;ПО;Комментарий\r\n"
    "Уральский федеральный университет;Базис;Базис;Ждём подписи ректора\r\n"
    "Южный федеральный университет;Loginom;Loginom;Ёлки-палки, всё в порядке\r\n"
)


@pytest.mark.parametrize(
    ("codec", "expected"),
    [
        ("utf-8-sig", "utf-8"),
        ("utf-8", "utf-8"),
        ("cp1251", "windows-1251"),
        ("koi8_r", "koi8-r"),
        ("cp866", "cp866"),
        ("utf-16", "utf-16"),
    ],
)
def test_russian_csv_is_read_in_every_common_encoding(codec: str, expected: str) -> None:
    content = EXPORT.encode(codec)

    sheet = read("Выгрузка.csv", content)

    assert detect_encoding(content) == expected
    assert sheet.encoding == expected
    assert sheet.delimiter == ";"
    assert sheet.headers == ["Название ВУЗа", "Вендор", "ПО", "Комментарий"]
    assert sheet.rows[1]["Комментарий"] == "Ёлки-палки, всё в порядке"


@pytest.mark.parametrize("codec", ["utf-8", "cp1251"])
def test_typographic_symbols_survive(codec: str) -> None:
    # «Ёлочки», номер и тире есть в cp1251, но не в KOI8-R и cp866.
    content = "Договор;Статус\r\n№ 12/2026 — «Базис»;Подписан\r\n".encode(codec)

    assert read("Выгрузка.csv", content).rows == [
        {"Договор": "№ 12/2026 — «Базис»", "Статус": "Подписан"}
    ]


def test_excel_separator_hint_and_multiline_cells() -> None:
    content = (
        'sep=,\r\nВуз,Комментарий\r\n"МГТУ","Первая строка\r\nвторая строка, с запятой"\r\n'
    ).encode("cp1251")

    sheet = read("Выгрузка.csv", content)

    assert sheet.delimiter == ","
    assert sheet.rows == [
        {"Вуз": "МГТУ", "Комментарий": "Первая строка\r\nвторая строка, с запятой"}
    ]


def test_wrong_encoding_is_refused_instead_of_garbling() -> None:
    with pytest.raises(SheetError, match="utf-8"):
        read("Выгрузка.csv", EXPORT.encode("cp1251"), encoding="utf-8")


def test_binary_file_named_csv_is_refused() -> None:
    with pytest.raises(SheetError, match="не текстовый"):
        read("Выгрузка.csv", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")


async def upload(
    client: AsyncClient, name: str, content: bytes, encoding: str | None = None
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/imports",
        files={"file": (name, content, "text/csv")},
        data={"encoding": encoding} if encoding else None,
        headers=as_user(ROMAN_MANAGER),
    )
    assert response.status_code == 201, response.text
    batch: dict[str, Any] = response.json()
    return batch


async def previewed(client: AsyncClient, batch: dict[str, Any]) -> dict[str, Any]:
    response = await client.put(
        f"/api/v1/imports/{batch['id']}/mapping",
        json={"column_map": batch["suggested_map"]},
        headers=as_user(ROMAN_MANAGER),
    )
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


async def test_csv_from_1c_imports_like_the_workbook(client: AsyncClient) -> None:
    today = date.today()
    from_csv = await upload(client, "Выгрузка.csv", build_csv(today, "cp1251", ";"))
    from_xlsx = await upload(client, "Выгрузка.xlsx", build_workbook(today))

    csv_preview = await previewed(client, from_csv)
    xlsx_preview = await previewed(client, from_xlsx)
    applied = await client.post(
        f"/api/v1/imports/{from_csv['id']}/apply", headers=as_user(ROMAN_MANAGER)
    )
    found = await client.get(
        "/api/v1/interactions",
        params={"search": "Московский физико-технический"},
        headers=as_user(ROMAN_MANAGER),
    )

    assert (from_csv["file_kind"], from_csv["encoding"], from_csv["delimiter"]) == (
        "csv",
        "windows-1251",
        ";",
    )
    assert from_csv["headers"] == list(HEADERS)
    assert csv_preview["stats"] == xlsx_preview["stats"]
    assert applied.json()["created"] == 25
    assert (
        found.json()["items"][0]["counterparty"]["name"] == "Московский физико-технический институт"
    )


async def test_encoding_can_be_chosen_by_hand(client: AsyncClient) -> None:
    batch = await upload(client, "Выгрузка.csv", build_csv(encoding="koi8_r"), encoding="koi8-r")

    assert batch["encoding"] == "koi8-r"
    assert batch["headers"] == list(HEADERS)


async def report_rows(
    client: AsyncClient, fmt: str, columns: list[str], **params: Any
) -> tuple[bytes, str]:
    job = await client.post(
        "/api/v1/reports",
        json={"format": fmt, "columns": columns, **params},
        headers=as_user(ANNA_KAM),
    )
    assert job.status_code == 202, job.text
    file = await client.get(f"/api/v1/reports/{job.json()['id']}/file", headers=as_user(ANNA_KAM))
    assert file.status_code == 200, file.text
    return file.content, file.headers["content-type"]


COLUMNS = ["counterparty", "program", "product", "stage", "owner"]


@pytest.mark.parametrize(
    ("fmt", "params", "media"),
    [
        ("csv", {"encoding": "utf-8"}, "text/csv; charset=utf-8"),
        ("csv", {"encoding": "windows-1251"}, "text/csv; charset=windows-1251"),
        ("xlsx", {}, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ("xls", {}, "application/vnd.ms-excel"),
    ],
)
async def test_report_reads_back_without_losing_cyrillic(
    client: AsyncClient, fmt: str, params: dict[str, str], media: str
) -> None:
    reference, _ = await report_rows(client, "json", COLUMNS)
    content, content_type = await report_rows(client, fmt, COLUMNS, **params)

    sheet = read(f"Отчёт.{fmt}", content)

    assert content_type == media
    assert sheet.rows == json.loads(reference)
    if fmt == "csv":
        assert sheet.encoding == params["encoding"]


async def test_formula_like_names_do_not_become_formulas(
    client: AsyncClient, session: AsyncSession
) -> None:
    await session.execute(
        update(University)
        .where(University.short_name == "МГТУ")
        .values(name='=HYPERLINK("http://example.com","МГТУ")')
    )
    await session.commit()
    columns = ["university"]

    xlsx, _ = await report_rows(client, "xlsx", columns)
    csv_file, _ = await report_rows(client, "csv", columns, encoding="utf-8")
    raw, _ = await report_rows(client, "json", columns)

    workbook = openpyxl.load_workbook(io.BytesIO(xlsx))
    cells = [row[0] for row in workbook.active.iter_rows(min_row=2, values_only=True)]
    assert '\'=HYPERLINK("http://example.com","МГТУ")' in cells
    assert "'=HYPERLINK" in csv_file.decode("utf-8-sig")
    # JSON — данные, а не таблица для Excel: значение отдаётся как есть.
    assert {"Вуз": '=HYPERLINK("http://example.com","МГТУ")'} in json.loads(raw)


def test_too_long_file_is_refused_not_cut() -> None:
    lines = ["ФИО;Email"] + [f"Иванов {index};i{index}@example.com" for index in range(6000)]
    content = ("\r\n".join(lines) + "\r\n").encode()

    # Раньше читались первые 5000 строк, а остальные молча пропадали.
    with pytest.raises(SheetError, match="больше 5000 строк"):
        read("список.csv", content)
