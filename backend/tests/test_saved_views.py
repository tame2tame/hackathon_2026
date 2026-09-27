"""Сохранённые виды: свои фильтры под своим названием."""

import pytest
from httpx import AsyncClient

from app.modules.views import service as views_service
from tests.users import ANNA_KAM, MIKHAIL_KAM, as_user

VIEWS = "/api/v1/saved-views"
OVERDUE = {
    "page": "interactions",
    "name": "Просроченные мои",
    "filters": {"stage_code": ["signing"], "has_open_signals": True},
    "columns": ["university", "program", "days_on_stage"],
}


async def test_view_is_saved_and_returned_to_its_owner(client: AsyncClient) -> None:
    created = await client.post(VIEWS, json=OVERDUE, headers=as_user(ANNA_KAM))

    mine = await client.get(VIEWS, params={"page": "interactions"}, headers=as_user(ANNA_KAM))
    other_page = await client.get(VIEWS, params={"page": "radar"}, headers=as_user(ANNA_KAM))
    foreign = await client.get(VIEWS, headers=as_user(MIKHAIL_KAM))

    assert created.status_code == 201, created.text
    assert created.json()["filters"] == OVERDUE["filters"]
    assert [item["name"] for item in mine.json()] == ["Просроченные мои"]
    assert other_page.json() == []
    # Вид — личная настройка: у соседа его нет.
    assert foreign.json() == []


async def test_name_is_not_taken_twice(client: AsyncClient) -> None:
    first = await client.post(VIEWS, json=OVERDUE, headers=as_user(ANNA_KAM))
    again = await client.post(VIEWS, json=OVERDUE, headers=as_user(ANNA_KAM))
    by_neighbour = await client.post(VIEWS, json=OVERDUE, headers=as_user(MIKHAIL_KAM))
    another_page = await client.post(
        VIEWS, json={**OVERDUE, "page": "radar"}, headers=as_user(ANNA_KAM)
    )

    assert first.status_code == 201
    assert again.status_code == 422
    assert again.json()["code"] == "VALIDATION_ERROR"
    # Одно и то же название у разных людей и на разных страницах — не конфликт.
    assert by_neighbour.status_code == 201
    assert another_page.status_code == 201


async def test_view_is_renamed_and_deleted(client: AsyncClient) -> None:
    view = (await client.post(VIEWS, json=OVERDUE, headers=as_user(ANNA_KAM))).json()

    renamed = await client.patch(
        f"{VIEWS}/{view['id']}",
        json={"name": "Горящее", "filters": {"days_on_stage_min": 30}},
        headers=as_user(ANNA_KAM),
    )
    by_neighbour = await client.patch(
        f"{VIEWS}/{view['id']}", json={"name": "Чужое"}, headers=as_user(MIKHAIL_KAM)
    )
    deleted = await client.delete(f"{VIEWS}/{view['id']}", headers=as_user(ANNA_KAM))
    after = await client.get(VIEWS, headers=as_user(ANNA_KAM))

    assert (renamed.json()["name"], renamed.json()["filters"]) == (
        "Горящее",
        {"days_on_stage_min": 30},
    )
    # Колонки не передавали — остались прежними.
    assert renamed.json()["columns"] == OVERDUE["columns"]
    assert by_neighbour.status_code == 404
    assert deleted.status_code == 204
    assert after.json() == []


async def test_view_does_not_become_a_storage(client: AsyncClient) -> None:
    fat = await client.post(
        VIEWS,
        json={**OVERDUE, "filters": {"junk": "я" * 5000}},
        headers=as_user(ANNA_KAM),
    )
    unknown_page = await client.post(
        VIEWS, json={**OVERDUE, "page": "чужая страница"}, headers=as_user(ANNA_KAM)
    )

    assert fat.status_code == 422
    assert fat.json()["errors"][0]["field"] == "filters"
    assert unknown_page.status_code == 422


async def test_columns_are_names_not_a_place_to_store_things(client: AsyncClient) -> None:
    fat_column = await client.post(
        VIEWS,
        json={**OVERDUE, "columns": ["university", "я" * 5000]},
        headers=as_user(ANNA_KAM),
    )
    many = await client.post(
        VIEWS,
        json={**OVERDUE, "name": "Много колонок", "columns": [f"c{i}" for i in range(60)]},
        headers=as_user(ANNA_KAM),
    )
    patched = await client.post(
        VIEWS, json={**OVERDUE, "name": "Обычный"}, headers=as_user(ANNA_KAM)
    )
    fat_patch = await client.patch(
        f"{VIEWS}/{patched.json()['id']}",
        json={"columns": ["я" * 5000]},
        headers=as_user(ANNA_KAM),
    )

    assert fat_column.status_code == 422
    assert many.status_code == 422
    assert fat_patch.status_code == 422


async def test_rename_race_ends_with_validation_error(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await client.post(VIEWS, json=OVERDUE, headers=as_user(ANNA_KAM))
    other = await client.post(VIEWS, json={**OVERDUE, "name": "Другой"}, headers=as_user(ANNA_KAM))

    # Второе переименование пришло, пока первое не зафиксировано: проверка его не видит.
    async def not_taken(*args: object, **kwargs: object) -> bool:
        return False

    monkeypatch.setattr(views_service, "_taken", not_taken)
    renamed = await client.patch(
        f"{VIEWS}/{other.json()['id']}",
        json={"name": OVERDUE["name"]},
        headers=as_user(ANNA_KAM),
    )

    assert renamed.status_code == 422
    assert renamed.json()["errors"] == [{"field": "name", "message": "Название занято"}]


async def test_blank_name_is_refused(client: AsyncClient) -> None:
    created = await client.post(VIEWS, json={**OVERDUE, "name": "   "}, headers=as_user(ANNA_KAM))
    other = await client.post(VIEWS, json=OVERDUE, headers=as_user(ANNA_KAM))
    renamed = await client.patch(
        f"{VIEWS}/{other.json()['id']}", json={"name": " "}, headers=as_user(ANNA_KAM)
    )

    assert created.status_code == 422
    assert renamed.status_code == 422
