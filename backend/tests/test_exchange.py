"""Двусторонняя интеграция: документ обмена, очередь отправки и приём на заглушках LMS и сайта."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations.clients import (
    ApplicationRecord,
    HttpSiteClient,
    MoodleLmsClient,
    PushResult,
)
from app.modules.integrations.models import IntegrationOutbox, IntegrationSource
from app.modules.integrations.outbox import mark_changed, push_source
from app.modules.integrations.service import ensure_sources, sync_source
from app.modules.interactions.models import Interaction
from mocks import lms as lms_mock
from mocks import site as site_mock
from tests.api import find, stage_id, upload_pdf
from tests.users import ALINA_ADMIN, ANNA_KAM, MIKHAIL_KAM, ROMAN_MANAGER, as_user


async def sources(session: AsyncSession) -> dict[str, IntegrationSource]:
    await ensure_sources(session)
    return {source.kind: source for source in await session.scalars(select(IntegrationSource))}


async def move_kfu(client: AsyncClient) -> dict[str, Any]:
    """Анна переводит КФУ со встречи на обмен документами."""
    kfu = await find(client, ANNA_KAM, search="КФУ")
    response = await client.post(
        f"/api/v1/interactions/{kfu['id']}/transitions",
        json={
            "to_stage_id": await stage_id(client, "documents_exchange"),
            "comment": "Встретились, отправили проект договора",
            "expected_version": kfu["version"],
        },
        headers=as_user(ANNA_KAM),
    )
    assert response.status_code == 201, response.text
    return kfu


async def outbox(session: AsyncSession, **filters: Any) -> list[IntegrationOutbox]:
    stmt = select(IntegrationOutbox).filter_by(**filters)
    return list(await session.scalars(stmt))


async def test_document_carries_status_owner_counterparty_and_links(client: AsyncClient) -> None:
    mgtu = await find(client, ANNA_KAM, stage_code="signing")
    attachment = await upload_pdf(client, ANNA_KAM, mgtu["id"], document_type="signed_contract")

    response = await client.get(
        f"/api/v1/interactions/{mgtu['id']}/export", headers=as_user(ANNA_KAM)
    )
    foreign = await client.get(
        f"/api/v1/interactions/{mgtu['id']}/export", headers=as_user(MIKHAIL_KAM)
    )

    assert response.status_code == 200, response.text
    document = response.json()
    assert document["format"] == "radar-vuzov/interaction@1"
    assert document["record"] == {"table": "interaction", "id": mgtu["id"], "version": 1}
    assert document["group"]["code"] == "universities"
    assert (document["status"]["state"], document["status"]["stage_code"]) == ("active", "signing")
    assert document["owner"]["full_name"] == "Анна Смирнова"
    assert (document["counterparty"]["kind"], document["counterparty"]["short_name"]) == (
        "university",
        "МГТУ",
    )
    assert document["program"]["direction_code"] == "devops"
    assert document["product"] == {
        "id": document["product"]["id"],
        "name": "Базис",
        "vendor_name": "Базис",
    }
    [file] = document["files"]
    assert file["id"] == attachment["id"]
    assert file["stage_code"] == "signing"
    assert file["storage"] == {
        "backend": "local",
        "key": f"interactions/{mgtu['id']}/{attachment['id']}",
    }
    assert foreign.status_code == 404


async def test_exchange_returns_only_records_changed_since(
    client: AsyncClient, session: AsyncSession
) -> None:
    before = await session.scalar(select(func.max(Interaction.updated_at)))
    assert before is not None
    kfu = await move_kfu(client)

    everything = await client.get("/api/v1/exchange/interactions", headers=as_user(ALINA_ADMIN))
    changed = await client.get(
        "/api/v1/exchange/interactions",
        params={"updated_since": (before + timedelta(microseconds=1)).isoformat()},
        headers=as_user(ALINA_ADMIN),
    )
    own = await client.get("/api/v1/exchange/interactions", headers=as_user(MIKHAIL_KAM))

    assert everything.json()["total"] == 6
    assert [item["record"]["id"] for item in changed.json()["items"]] == [kfu["id"]]
    assert changed.json()["items"][0]["status"]["stage_code"] == "documents_exchange"
    assert own.json()["total"] == 2


async def test_changes_are_queued_once_per_record_and_receiver(
    client: AsyncClient, session: AsyncSession
) -> None:
    await sources(session)

    kfu = await move_kfu(client)
    await upload_pdf(client, ANNA_KAM, kfu["id"])

    pending = await outbox(session, status="pending")
    assert len(pending) == 2
    # Очередь не раздувается, но второе изменение не теряется: причина свежая, счётчик вырос.
    assert {entry.reason for entry in pending} == {"attachment"}
    assert {entry.change_seq for entry in pending} == {1}


async def test_push_delivers_documents_to_the_lms_and_site_mocks(
    client: AsyncClient, session: AsyncSession
) -> None:
    by_kind = await sources(session)
    kfu = await move_kfu(client)
    receivers = {
        "site": (
            HttpSiteClient("http://mock-site", transport=httpx.ASGITransport(app=site_mock.app)),
            site_mock.app,
        ),
        "lms": (
            MoodleLmsClient("http://mock-lms", transport=httpx.ASGITransport(app=lms_mock.app)),
            lms_mock.app,
        ),
    }

    for kind, (receiver, app) in receivers.items():
        run = await push_source(session, by_kind[kind], client=receiver)

        assert (run.direction, run.status, run.stats) == ("push", "done", {"sent": 1})
        assert by_kind[kind].last_push_at is not None
        async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://m") as mock:
            received = (await mock.get("/api/crm/interactions")).json()
        document = next(item for item in received if item["record"]["id"] == kfu["id"])
        assert document["status"]["stage_code"] == "documents_exchange"

    assert await outbox(session, status="pending") == []
    assert len(await outbox(session, status="sent")) == 2


async def test_unavailable_receiver_is_retried_later(
    client: AsyncClient, session: AsyncSession
) -> None:
    site = (await sources(session))["site"]
    await move_kfu(client)
    broken = HttpSiteClient(
        "http://mock-site", transport=httpx.MockTransport(lambda request: httpx.Response(503))
    )
    moment = datetime.now(UTC)

    failed = await push_source(session, site, client=broken, now=moment)
    too_early = await push_source(session, site, client=broken, now=moment)

    assert (failed.status, failed.error_code) == ("failed", "INTEGRATION_UNAVAILABLE")
    [entry] = await outbox(session, source_id=site.id)
    assert (entry.status, entry.attempts) == ("pending", 1)
    assert entry.next_attempt_at > moment
    assert (too_early.status, too_early.stats) == ("done", {"sent": 0})


async def test_rejected_document_waits_for_a_human(
    client: AsyncClient, session: AsyncSession
) -> None:
    lms = (await sources(session))["lms"]
    kfu = await move_kfu(client)

    class Rejecting:
        async def push_interactions(self, documents: list[dict[str, Any]]) -> PushResult:
            return PushResult(frozenset(), {kfu["id"]: "В LMS нет курса программы"})

    run = await push_source(session, lms, client=Rejecting())

    [entry] = await outbox(session, source_id=lms.id)
    assert run.stats == {"sent": 0, "rejected": 1}
    assert (entry.status, entry.last_error) == ("failed", "В LMS нет курса программы")


async def test_manager_pushes_by_hand_and_reads_the_queue(
    client: AsyncClient, session: AsyncSession
) -> None:
    site = (await sources(session))["site"]
    await move_kfu(client)

    # Адрес сайта в тестах мёртвый: запуск честно падает и остаётся в журнале.
    pushed = await client.post(
        f"/api/v1/integrations/{site.id}/push", headers=as_user(ROMAN_MANAGER)
    )
    queue = await client.get(
        f"/api/v1/integrations/{site.id}/outbox",
        params={"status": "pending"},
        headers=as_user(ROMAN_MANAGER),
    )
    runs = await client.get(f"/api/v1/integrations/{site.id}/runs", headers=as_user(ROMAN_MANAGER))
    by_kam = await client.post(f"/api/v1/integrations/{site.id}/push", headers=as_user(ANNA_KAM))

    assert pushed.status_code == 200, pushed.text
    assert (pushed.json()["direction"], pushed.json()["status"]) == ("push", "failed")
    [entry] = queue.json()
    assert (entry["reason"], entry["attempts"]) == ("transition", 1)
    assert runs.json()[0]["direction"] == "push"
    assert by_kam.status_code == 403


async def test_admin_stops_pushing_to_a_source(client: AsyncClient, session: AsyncSession) -> None:
    by_kind = await sources(session)

    by_manager = await client.patch(
        f"/api/v1/integrations/{by_kind['lms'].id}",
        json={"push_enabled": False},
        headers=as_user(ROMAN_MANAGER),
    )
    by_admin = await client.patch(
        f"/api/v1/integrations/{by_kind['lms'].id}",
        json={"push_enabled": False},
        headers=as_user(ALINA_ADMIN),
    )
    await move_kfu(client)

    assert by_manager.status_code == 403
    assert by_admin.json()["push_enabled"] is False
    assert [entry.source_id for entry in await outbox(session)] == [by_kind["site"].id]


async def test_site_learns_where_its_application_went(session: AsyncSession) -> None:
    site = (await sources(session))["site"]

    class OneApplication:
        async def fetch_applications(self) -> list[ApplicationRecord]:
            return [
                ApplicationRecord(
                    "site-77", "ИТМО", "Анализ данных", "Приёмная", None, datetime.now(UTC)
                )
            ]

    await sync_source(session, site, client=OneApplication())

    [entry] = await outbox(session, source_id=site.id)
    assert entry.reason == "site_application"
    captured: list[dict[str, Any]] = []

    class Capturing:
        async def push_interactions(self, documents: list[dict[str, Any]]) -> PushResult:
            captured.extend(documents)
            return PushResult(frozenset(item["record"]["id"] for item in documents), {})

    await push_source(session, site, client=Capturing())

    [document] = captured
    assert [item["external_id"] for item in document["site_applications"]] == ["site-77"]
    assert document["status"]["stage_code"] == "contact_search"


async def test_change_during_push_is_sent_again(client: AsyncClient, session: AsyncSession) -> None:
    site = (await sources(session))["site"]
    kfu = await move_kfu(client)

    class Accepting:
        def __init__(self, change_meanwhile: bool) -> None:
            self.change_meanwhile = change_meanwhile

        async def push_interactions(self, documents: list[dict[str, Any]]) -> PushResult:
            if self.change_meanwhile:
                # Пока документ летел к получателю, КАМ изменил запись ещё раз.
                await mark_changed(session, [uuid.UUID(kfu["id"])], "transition")
            return PushResult(frozenset(item["record"]["id"] for item in documents), {})

    during = await push_source(session, site, client=Accepting(change_meanwhile=True))
    [entry] = await outbox(session, source_id=site.id)
    after_first = (entry.status, entry.change_seq)
    later = await push_source(session, site, client=Accepting(change_meanwhile=False))

    # Изменение, сделанное во время отправки, не теряется: запись уходит ещё раз.
    assert during.stats == {"sent": 0, "changed": 1}
    assert after_first == ("pending", 1)
    assert later.stats == {"sent": 1}
    assert [item.status for item in await outbox(session, source_id=site.id)] == ["sent"]


async def test_long_outage_does_not_drop_the_change(
    client: AsyncClient, session: AsyncSession
) -> None:
    site = (await sources(session))["site"]
    await move_kfu(client)
    broken = HttpSiteClient(
        "http://mock-site", transport=httpx.MockTransport(lambda request: httpx.Response(503))
    )

    moment = datetime.now(UTC)
    for _ in range(20):
        moment += timedelta(hours=2)
        await push_source(session, site, client=broken, now=moment)
    [entry] = await outbox(session, source_id=site.id)

    # Раньше после восьми неудач изменение помечалось failed и больше не уходило никогда.
    assert (entry.status, entry.attempts) == ("pending", 20)
    assert entry.next_attempt_at - moment <= timedelta(minutes=60)
