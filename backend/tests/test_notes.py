"""Заметки по взаимодействию: доступ, проверка текста и влияние на сигнал о простое."""

from httpx import AsyncClient

from tests.api import find
from tests.users import ANNA_KAM, MIKHAIL_KAM, as_user


async def signals_of(client: AsyncClient, email: str, interaction_id: str) -> set[str]:
    card = await client.get(f"/api/v1/interactions/{interaction_id}", headers=as_user(email))
    assert card.status_code == 200
    return {signal["kind"] for signal in card.json()["signals"]}


async def test_note_is_added_and_listed(client: AsyncClient) -> None:
    item = await find(client, ANNA_KAM, stage_code="signing")

    created = await client.post(
        f"/api/v1/interactions/{item['id']}/notes",
        json={"text": "Договорились созвониться в пятницу"},
        headers=as_user(ANNA_KAM),
    )
    listed = await client.get(f"/api/v1/interactions/{item['id']}/notes", headers=as_user(ANNA_KAM))

    assert created.status_code == 201
    assert created.json()["author"]["full_name"] == "Анна Смирнова"
    assert [note["text"] for note in listed.json()] == ["Договорились созвониться в пятницу"]


async def test_note_closes_the_inactivity_signal(client: AsyncClient) -> None:
    # КФУ в демо-данных стоит без движения 23 дня, поэтому у него открыт сигнал о простое.
    item = await find(client, ANNA_KAM, search="КФУ")
    assert "inactivity" in await signals_of(client, ANNA_KAM, item["id"])

    await client.post(
        f"/api/v1/interactions/{item['id']}/notes",
        json={"text": "Связались с деканатом, ждём ответ"},
        headers=as_user(ANNA_KAM),
    )

    assert "inactivity" not in await signals_of(client, ANNA_KAM, item["id"])


async def test_foreign_interaction_has_no_notes(client: AsyncClient) -> None:
    foreign = await find(client, MIKHAIL_KAM, search="УрФУ")

    listed = await client.get(
        f"/api/v1/interactions/{foreign['id']}/notes", headers=as_user(ANNA_KAM)
    )
    created = await client.post(
        f"/api/v1/interactions/{foreign['id']}/notes",
        json={"text": "Чужая заметка"},
        headers=as_user(ANNA_KAM),
    )

    assert (listed.status_code, created.status_code) == (404, 404)


async def test_empty_note_is_refused(client: AsyncClient) -> None:
    item = await find(client, ANNA_KAM, stage_code="signing")

    response = await client.post(
        f"/api/v1/interactions/{item['id']}/notes",
        json={"text": ""},
        headers=as_user(ANNA_KAM),
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
