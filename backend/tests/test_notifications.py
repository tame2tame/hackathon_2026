"""Уведомления: эскалация зависших записей, смена этапа, лента, каналы и доставка на заглушках."""

import smtplib
import uuid
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from typing import Any

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import NOTIFICATION_CREATED, Event
from app.core.roles import Role
from app.core.security import CurrentUser
from app.modules.events.router import visible
from app.modules.notifications import channels
from app.modules.notifications.models import NotificationDelivery
from app.modules.notifications.service import MAX_ATTEMPTS, deliver_pending
from mocks import messengers
from tests.api import find, stage_id
from tests.test_workflow_editor import draft_without, publish
from tests.users import ALINA_ADMIN, ANNA_KAM, MIKHAIL_KAM, ROMAN_MANAGER, as_user

ADMIN = "/api/v1/admin"
NOTIFICATIONS = "/api/v1/notifications"


async def feed(client: AsyncClient, email: str, **params: Any) -> dict[str, Any]:
    response = await client.get(NOTIFICATIONS, params=params, headers=as_user(email))
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


async def escalate(client: AsyncClient) -> int:
    response = await client.post(f"{ADMIN}/escalations/run", headers=as_user(ALINA_ADMIN))
    assert response.status_code == 200, response.text
    notified: int = response.json()["notified"]
    return notified


async def enable_telegram(client: AsyncClient) -> None:
    response = await client.patch(
        f"{ADMIN}/notification-channels/telegram",
        json={"is_enabled": True, "settings": {"base_url": "http://mock-messengers"}},
        headers=as_user(ALINA_ADMIN),
    )
    assert response.status_code == 200, response.text


async def test_stalled_record_escalates_to_the_team_manager(client: AsyncClient) -> None:
    kfu = await find(client, ANNA_KAM, search="КФУ")

    first = await escalate(client)
    again = await escalate(client)

    assert (first, again) == (1, 0)
    [item] = (await feed(client, ROMAN_MANAGER))["items"]
    assert item["kind"] == "stalled_interaction"
    assert item["interaction_id"] == kfu["id"]
    assert item["title"] == "Запись без изменений 23 дня"
    assert "«КФУ — Веб-разработка»" in item["body"]
    assert item["body"].endswith("Задача долго стоит — уточните причину.")
    # Сам КАМ не получает эскалацию на себя.
    assert (await feed(client, ANNA_KAM))["total"] == 0


async def test_escalation_follows_the_setting(client: AsyncClient) -> None:
    async def configure(value: dict[str, Any]) -> None:
        response = await client.put(
            f"{ADMIN}/settings/stalled_escalation",
            json={"value": value},
            headers=as_user(ALINA_ADMIN),
        )
        assert response.status_code == 200, response.text

    await configure({"days": 30})
    later = await escalate(client)
    await configure({"days": 14, "notify_role": "admin"})
    to_admins = await escalate(client)
    await configure({"enabled": False})
    disabled = await escalate(client)

    assert (later, to_admins, disabled) == (0, 1, 0)
    assert (await feed(client, ALINA_ADMIN))["items"][0]["kind"] == "stalled_interaction"
    assert (await feed(client, ROMAN_MANAGER))["total"] == 0


async def test_stage_change_by_someone_else_notifies_the_owner(client: AsyncClient) -> None:
    ngu = await find(client, MIKHAIL_KAM, search="НГУ")
    kfu = await find(client, ANNA_KAM, search="КФУ")

    by_manager = await client.post(
        f"/api/v1/interactions/{ngu['id']}/transitions",
        json={
            "to_stage_id": await stage_id(client, "documents_revision"),
            "comment": "Вуз просит поправить приложение",
            "expected_version": ngu["version"],
        },
        headers=as_user(ROMAN_MANAGER),
    )
    by_owner = await client.post(
        f"/api/v1/interactions/{kfu['id']}/transitions",
        json={
            "to_stage_id": await stage_id(client, "documents_exchange"),
            "comment": "Встретились",
            "expected_version": kfu["version"],
        },
        headers=as_user(ANNA_KAM),
    )

    assert (by_manager.status_code, by_owner.status_code) == (201, 201)
    [item] = (await feed(client, MIKHAIL_KAM))["items"]
    assert item["kind"] == "stage_changed"
    assert item["title"] == "Запись переведена на этап «Доработка документов»"
    assert item["body"].startswith("Роман Ковалёв перевёл(а) «НГУ — DevOps-инженерия»")
    assert item["body"].endswith("Комментарий: Вуз просит поправить приложение")
    assert (await feed(client, ANNA_KAM))["total"] == 0


async def test_workflow_change_tells_owners_where_records_went(
    client: AsyncClient, session: AsyncSession
) -> None:
    draft = await draft_without(client, session, {"meeting"})

    response = await publish(client, draft)

    assert response.status_code == 200, response.text
    [item] = (await feed(client, ANNA_KAM))["items"]
    assert item["kind"] == "workflow_changed"
    assert item["title"] == "Процесс изменён: записей на другом этапе — 1"
    assert "«Встреча» → «Коммуникация»: 1" in item["body"]
    # У Михаила записи остались на своих этапах — сообщать нечего.
    assert (await feed(client, MIKHAIL_KAM))["total"] == 0


async def test_feed_marks_read_and_hides_other_people(client: AsyncClient) -> None:
    await escalate(client)
    [item] = (await feed(client, ROMAN_MANAGER, unread=True))["items"]

    foreign = await client.post(f"{NOTIFICATIONS}/{item['id']}/read", headers=as_user(ANNA_KAM))
    read = await client.post(f"{NOTIFICATIONS}/{item['id']}/read", headers=as_user(ROMAN_MANAGER))
    read_all = await client.post(f"{NOTIFICATIONS}/read-all", headers=as_user(ROMAN_MANAGER))

    assert foreign.status_code == 404
    assert read.json()["read_at"] is not None
    assert read_all.json() == {"updated": 0}
    assert (await feed(client, ROMAN_MANAGER, unread=True))["total"] == 0


def test_notification_event_reaches_only_its_addressee() -> None:
    anna = uuid.uuid4()
    event = Event("1", NOTIFICATION_CREATED, {"title": "Лично"}, owner_user_id=anna)

    def user(role: Role, user_id: uuid.UUID | None = None) -> CurrentUser:
        return CurrentUser(user_id or uuid.uuid4(), "x@example.com", "X", role, team_id=None)

    assert visible(event, user(Role.KAM, anna), set())
    assert not visible(event, user(Role.MANAGER), {anna})
    assert not visible(event, user(Role.ADMIN), set())


async def test_escalation_is_delivered_to_telegram_through_the_mock(
    client: AsyncClient, session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(channels, "http_transport", httpx.ASGITransport(app=messengers.app))
    await enable_telegram(client)

    await escalate(client)
    stats = await deliver_pending(session, datetime.now(UTC))

    assert (stats.sent, stats.retried, stats.failed) == (1, 0, 0)
    async with AsyncClient(
        transport=httpx.ASGITransport(app=messengers.app), base_url="http://mock"
    ) as mock:
        received = (await mock.get("/sent", params={"channel": "telegram"})).json()
    # Адрес руководителя в Telegram заведён демо-данными.
    assert any(
        message["address"] == "100200300" and "Запись без изменений" in message["text"]
        for message in received
    )
    journal = await client.get(
        f"{ADMIN}/notification-deliveries", params={"status": "sent"}, headers=as_user(ALINA_ADMIN)
    )
    assert [entry["channel_kind"] for entry in journal.json()] == ["telegram"]


async def test_failed_delivery_is_retried_and_then_given_up(
    client: AsyncClient, session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        channels, "http_transport", httpx.MockTransport(lambda request: httpx.Response(502))
    )
    await enable_telegram(client)
    await escalate(client)

    moment = datetime.now(UTC)
    first = await deliver_pending(session, moment)
    delivery = await session.scalar(select(NotificationDelivery))
    assert delivery is not None
    assert (first.retried, delivery.attempts) == (1, 1)
    assert delivery.next_attempt_at > moment
    # Раньше паузы повторной попытки нет.
    assert (await deliver_pending(session, moment)).retried == 0

    for _ in range(MAX_ATTEMPTS - 1):
        moment += timedelta(hours=2)
        await deliver_pending(session, moment)

    await session.refresh(delivery)
    assert (delivery.status, delivery.attempts) == ("failed", MAX_ATTEMPTS)
    assert delivery.last_error == "HTTPStatusError"


async def test_admin_checks_a_channel_with_a_test_message(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(channels, "http_transport", httpx.ASGITransport(app=messengers.app))
    without_address = await client.post(
        f"{ADMIN}/notification-channels/max/test", headers=as_user(ALINA_ADMIN)
    )
    address = await client.put(
        "/api/v1/me/notification-addresses/max",
        json={"address": "700800900"},
        headers=as_user(ALINA_ADMIN),
    )
    sent = await client.post(
        f"{ADMIN}/notification-channels/max/test", headers=as_user(ALINA_ADMIN)
    )

    assert without_address.status_code == 422
    assert address.json()["channel_enabled"] is False
    assert sent.status_code == 200, sent.text
    assert sent.json()["status"] == "sent"


async def test_addresses_and_channel_settings_are_validated(client: AsyncClient) -> None:
    bad_address = await client.put(
        "/api/v1/me/notification-addresses/telegram",
        json={"address": "@anna"},
        headers=as_user(ANNA_KAM),
    )
    foreign_secret = await client.patch(
        f"{ADMIN}/notification-channels/telegram",
        json={"secret_ref": "DATABASE_URL"},
        headers=as_user(ALINA_ADMIN),
    )
    bad_url = await client.patch(
        f"{ADMIN}/notification-channels/telegram",
        json={"settings": {"base_url": "ftp://example.com"}},
        headers=as_user(ALINA_ADMIN),
    )
    by_manager = await client.get(f"{ADMIN}/notification-channels", headers=as_user(ROMAN_MANAGER))

    assert bad_address.status_code == 422
    assert bad_address.json()["errors"][0]["message"] == "Идентификатор чата Telegram — число"
    assert foreign_secret.status_code == 422
    assert bad_url.json()["errors"][0]["field"] == "settings.base_url"
    assert by_manager.status_code == 403


async def test_email_sender_writes_a_plain_letter(monkeypatch: pytest.MonkeyPatch) -> None:
    letters: list[EmailMessage] = []

    class FakeSMTP:
        def __init__(self, host: str, port: int, timeout: float) -> None:
            self.address = (host, port)

        def __enter__(self) -> "FakeSMTP":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def send_message(self, message: EmailMessage) -> None:
            letters.append(message)

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)

    await channels.EmailSender("smtp.example.com", 25, "radar@example.com").send(
        channels.OutgoingMessage("roman.kovalev@example.com", "Заголовок", "Текст", "http://x/1")
    )

    [letter] = letters
    assert letter["To"] == "roman.kovalev@example.com"
    assert letter["Subject"] == "Заголовок"
    assert letter.get_content().strip() == "Заголовок\n\nТекст\n\nhttp://x/1"


async def test_demo_manager_has_addresses_for_the_stubs(client: AsyncClient) -> None:
    response = await client.get("/api/v1/me/notification-addresses", headers=as_user(ROMAN_MANAGER))

    by_kind = {item["channel_kind"]: item for item in response.json()}
    assert by_kind["telegram"]["address"] == "100200300"
    assert by_kind["email"]["address"] == ROMAN_MANAGER
    assert by_kind["max"]["address"] is None
