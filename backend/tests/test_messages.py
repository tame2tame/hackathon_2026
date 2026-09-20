"""Переписка внутри сервиса: диалоги, непрочитанные и ссылка на запись."""

from typing import Any

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.api import find, user_id
from tests.users import ALINA_ADMIN, ANNA_KAM, MIKHAIL_KAM, ROMAN_MANAGER, as_user

MESSAGES = "/api/v1/messages"


async def send(
    client: AsyncClient, email: str, recipient: str, body: str, **extra: Any
) -> dict[str, Any]:
    response = await client.post(
        MESSAGES, json={"recipient_id": recipient, "body": body, **extra}, headers=as_user(email)
    )
    assert response.status_code == 201, response.text
    message: dict[str, Any] = response.json()
    return message


async def test_kam_and_manager_talk_about_a_record(
    client: AsyncClient, session: AsyncSession
) -> None:
    manager = str(await user_id(session, ROMAN_MANAGER))
    anna = str(await user_id(session, ANNA_KAM))
    mgtu = await find(client, ANNA_KAM, stage_code="signing")

    asked = await send(
        client, ANNA_KAM, manager, "МГТУ тянет с подписью, подключишься?", interaction_id=mgtu["id"]
    )
    answered = await send(client, ROMAN_MANAGER, anna, "Позвоню проректору завтра")
    dialog = await client.get(f"{MESSAGES}/{manager}", headers=as_user(ANNA_KAM))

    assert asked["interaction"]["id"] == mgtu["id"]
    assert " — " in asked["interaction"]["label"]
    assert asked["read_at"] is None
    # Читаем сверху вниз: сначала вопрос, потом ответ.
    assert [item["body"] for item in dialog.json()] == [asked["body"], answered["body"]]
    assert dialog.json()[0]["sender"]["full_name"] == "Анна Смирнова"


async def test_unread_counter_drops_after_reading(
    client: AsyncClient, session: AsyncSession
) -> None:
    anna = str(await user_id(session, ANNA_KAM))
    manager = str(await user_id(session, ROMAN_MANAGER))
    await send(client, ROMAN_MANAGER, anna, "Посмотри КФУ")
    await send(client, ROMAN_MANAGER, anna, "И ИТМО тоже")

    before = await client.get(MESSAGES, headers=as_user(ANNA_KAM))
    read = await client.post(f"{MESSAGES}/{manager}/read", headers=as_user(ANNA_KAM))
    after = await client.get(MESSAGES, headers=as_user(ANNA_KAM))
    by_sender = await client.get(MESSAGES, headers=as_user(ROMAN_MANAGER))

    assert before.json()["unread_total"] == 2
    assert before.json()["items"][0]["last_message"] == "И ИТМО тоже"
    assert read.json()["updated"] == 2
    assert after.json()["unread_total"] == 0
    # Свои отправленные непрочитанными не считаются.
    assert by_sender.json()["unread_total"] == 0


async def test_foreign_conversation_is_not_visible(
    client: AsyncClient, session: AsyncSession
) -> None:
    anna = str(await user_id(session, ANNA_KAM))
    mikhail = str(await user_id(session, MIKHAIL_KAM))
    await send(client, ANNA_KAM, mikhail, "Это между нами двоими")

    outsider_dialogs = await client.get(MESSAGES, headers=as_user(ALINA_ADMIN))
    outsider_dialog = await client.get(f"{MESSAGES}/{anna}", headers=as_user(ALINA_ADMIN))

    # Даже администратор видит только свою переписку: чужая — не его дело.
    assert outsider_dialogs.json() == {"unread_total": 0, "items": []}
    assert outsider_dialog.json() == []


async def test_link_to_a_record_appears_only_for_those_who_see_it(
    client: AsyncClient, session: AsyncSession
) -> None:
    mikhail = str(await user_id(session, MIKHAIL_KAM))
    mgtu = await find(client, ANNA_KAM, stage_code="signing")

    anna = str(await user_id(session, ANNA_KAM))
    sent = await send(
        client, ANNA_KAM, mikhail, "Посмотри, как мы дожали", interaction_id=mgtu["id"]
    )
    for_recipient = await client.get(f"{MESSAGES}/{anna}", headers=as_user(MIKHAIL_KAM))

    assert sent["interaction"] is not None
    # Михаилу запись недоступна: текст он видит, ссылку на чужую карточку — нет.
    assert for_recipient.json()[0]["body"] == "Посмотри, как мы дожали"
    assert for_recipient.json()[0]["interaction"] is None


async def test_record_of_a_stranger_cannot_be_attached(
    client: AsyncClient, session: AsyncSession
) -> None:
    anna = str(await user_id(session, ANNA_KAM))
    mgtu = await find(client, ANNA_KAM, stage_code="signing")

    response = await client.post(
        MESSAGES,
        json={"recipient_id": anna, "body": "Чья это запись?", "interaction_id": mgtu["id"]},
        headers=as_user(MIKHAIL_KAM),
    )

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


async def test_message_needs_a_real_colleague(client: AsyncClient, session: AsyncSession) -> None:
    anna = str(await user_id(session, ANNA_KAM))

    to_self = await client.post(
        MESSAGES, json={"recipient_id": anna, "body": "Напоминание себе"}, headers=as_user(ANNA_KAM)
    )
    to_nobody = await client.post(
        MESSAGES,
        json={"recipient_id": "00000000-0000-0000-0000-000000000000", "body": "Ау"},
        headers=as_user(ANNA_KAM),
    )
    empty = await client.post(
        MESSAGES, json={"recipient_id": anna, "body": "   "}, headers=as_user(ROMAN_MANAGER)
    )

    assert to_self.status_code == 422
    assert to_self.json()["errors"][0]["field"] == "recipient_id"
    assert to_nobody.status_code == 404
    assert empty.status_code == 201
