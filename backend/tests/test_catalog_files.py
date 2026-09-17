"""Справочники файлом: предпросмотр, применение без дублей, форматы и круговая выгрузка."""

import json
from io import BytesIO
from typing import Any

from httpx import AsyncClient
from openpyxl import Workbook

from app.modules.reports.renderers import render
from tests.users import ALINA_ADMIN, ROMAN_MANAGER, as_user

CATALOGS = "/api/v1/admin/catalogs"


async def load(
    client: AsyncClient,
    kind: str,
    name: str,
    content: bytes,
    *,
    dry_run: bool,
    email: str = ALINA_ADMIN,
    **form: str,
) -> dict[str, Any]:
    response = await client.post(
        f"{CATALOGS}/{kind}/import",
        files={"file": (name, content, "application/octet-stream")},
        data={"dry_run": str(dry_run).lower(), **form},
        headers=as_user(email),
    )
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


def universities_json(*names: str) -> bytes:
    items = [{"name": name, "region": "Томская область", "city": "Томск"} for name in names]
    return json.dumps(items, ensure_ascii=False).encode("utf-8")


async def university_names(client: AsyncClient) -> set[str]:
    response = await client.get(
        "/api/v1/universities", params={"page_size": 200}, headers=as_user(ALINA_ADMIN)
    )
    return {item["name"] for item in response.json()["items"]}


async def test_preview_changes_nothing_and_apply_creates(client: AsyncClient) -> None:
    content = universities_json("Томский государственный университет", "Университет ИТМО")

    preview = await load(client, "universities", "вузы.json", content, dry_run=True)
    after_preview = await university_names(client)
    applied = await load(client, "universities", "вузы.json", content, dry_run=False)
    again = await load(client, "universities", "вузы.json", content, dry_run=False)

    assert (preview["created"], preview["updated"], preview["dry_run"]) == (1, 1, True)
    assert "Томский государственный университет" not in after_preview
    assert (applied["created"], applied["updated"]) == (1, 1)
    assert "Томский государственный университет" in await university_names(client)
    # Повторная загрузка того же файла ничего не меняет.
    assert (again["created"], again["updated"], again["unchanged"]) == (0, 0, 2)


async def test_cp1251_table_with_russian_headers_adds_products_and_vendors(
    client: AsyncClient,
) -> None:
    content = "Вендор;Продукт\r\nРостелеком;Яга\r\nБазис;Базис\r\n".encode("cp1251")

    result = await load(client, "products", "продукты.csv", content, dry_run=False)
    exported = await client.get(
        f"{CATALOGS}/products/export", params={"format": "json"}, headers=as_user(ROMAN_MANAGER)
    )

    by_key = {row["key"]: row for row in result["rows"]}
    assert by_key["Ростелеком / Яга"]["action"] == "created"
    assert by_key["Ростелеком / Яга"]["detail"] == "добавлен вендор «Ростелеком»"
    assert by_key["Базис / Базис"]["action"] == "unchanged"
    assert {"vendor": "Ростелеком", "name": "Яга"} in exported.json()["items"]


async def test_program_links_are_checked_row_by_row(client: AsyncClient) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Код направления", "Программа", "Вендор", "Продукт", "По умолчанию"])
    sheet.append(["devops", "DevOps-инженерия", "Loginom", "Loginom", "нет"])
    sheet.append(["devops", "Нет такой программы", "Базис", "Базис", "да"])
    sheet.append(["devops", "DevOps-инженерия", "Базис", "Базис", "может быть"])
    buffer = BytesIO()
    workbook.save(buffer)

    result = await load(client, "program-products", "связи.xlsx", buffer.getvalue(), dry_run=False)

    actions = [(row["row_no"], row["action"]) for row in result["rows"]]
    assert actions == [(1, "created"), (2, "error"), (3, "error")]
    assert "Нет программы «Нет такой программы»" in result["rows"][1]["detail"]
    assert result["rows"][2]["detail"] == "Не понятно, да или нет: «может быть»"


async def test_export_loads_back_unchanged_in_every_format(client: AsyncClient) -> None:
    for fmt, params in (("csv", {"encoding": "windows-1251"}), ("xlsx", {}), ("json", {})):
        exported = await client.get(
            f"{CATALOGS}/directions/export",
            params={"format": fmt, **params},
            headers=as_user(ALINA_ADMIN),
        )
        assert exported.status_code == 200, exported.text

        result = await load(
            client, "directions", f"направления.{fmt}", exported.content, dry_run=True
        )

        assert result["errors"] == 0, (fmt, result["rows"])
        assert result["unchanged"] == 7
        assert result["created"] == result["updated"] == 0


async def test_problems_in_the_file_are_reported(client: AsyncClient) -> None:
    missing_column = render(
        "csv", ["Название", "Комментарий"], [["Без кода", "нет колонки «Код»"]], "x", "utf-8"
    )
    duplicate = json.dumps(
        [{"code": "qa", "name": "Тестирование"}, {"code": "QA", "name": "Ещё раз"}, {"code": ""}],
        ensure_ascii=False,
    ).encode("utf-8")

    no_column = await client.post(
        f"{CATALOGS}/directions/import",
        files={"file": ("направления.csv", missing_column, "text/csv")},
        headers=as_user(ALINA_ADMIN),
    )
    broken = await client.post(
        f"{CATALOGS}/directions/import",
        files={"file": ("направления.json", b"{not json", "application/json")},
        headers=as_user(ALINA_ADMIN),
    )
    unknown = await client.post(
        f"{CATALOGS}/planets/import",
        files={"file": ("x.json", b"[]", "application/json")},
        headers=as_user(ALINA_ADMIN),
    )
    by_manager = await client.post(
        f"{CATALOGS}/directions/import",
        files={"file": ("x.json", b"[]", "application/json")},
        headers=as_user(ROMAN_MANAGER),
    )
    rows = (await load(client, "directions", "d.json", duplicate, dry_run=True))["rows"]

    assert no_column.json()["code"] == "IMPORT_MAPPING_INVALID"
    assert broken.json()["code"] == "VALIDATION_ERROR"
    assert unknown.status_code == 404
    assert by_manager.status_code == 403
    assert [row["action"] for row in rows] == ["created", "error", "error"]
    assert rows[1]["detail"] == "Та же запись уже есть выше в файле"
