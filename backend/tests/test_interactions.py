from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from app.modules.audit.models import AuditLog
from app.modules.interactions.models import Interaction
from app.modules.workflow.models import Stage
from tests.api import find, stage_id, upload_pdf
from tests.users import ALINA_ADMIN, ANNA_KAM, MIKHAIL_KAM, ROMAN_MANAGER, as_user


@pytest.mark.parametrize(("email", "total"), [(ANNA_KAM, 4), (MIKHAIL_KAM, 2), (ROMAN_MANAGER, 6)])
async def test_list_follows_scope(client: AsyncClient, email: str, total: int) -> None:
    response = await client.get("/api/v1/interactions", headers=as_user(email))

    assert response.json()["total"] == total


async def test_filters_by_search_and_stage(client: AsyncClient) -> None:
    by_search = await find(client, ALINA_ADMIN, search="итмо")
    by_stage = await find(client, ALINA_ADMIN, stage_code="signing")

    assert by_search["university"]["short_name"] == "ИТМО"
    assert by_stage["university"]["short_name"] == "МГТУ"
    assert by_stage["days_on_stage"] == 41


async def test_period_filter_covers_active_and_past(client: AsyncClient) -> None:
    today = datetime.now(UTC).date()

    recent = await client.get(
        "/api/v1/interactions",
        params={"period_from": str(today - timedelta(days=90)), "period_to": str(today)},
        headers=as_user(ALINA_ADMIN),
    )
    long_ago = await client.get(
        "/api/v1/interactions",
        params={
            "period_from": str(today - timedelta(days=400)),
            "period_to": str(today - timedelta(days=365)),
        },
        headers=as_user(ALINA_ADMIN),
    )

    assert recent.json()["total"] == 6
    assert long_ago.json()["total"] == 0


async def test_card_has_history_transitions_and_signals(client: AsyncClient) -> None:
    item = await find(client, ANNA_KAM, stage_code="signing")

    response = await client.get(f"/api/v1/interactions/{item['id']}", headers=as_user(ANNA_KAM))

    assert response.status_code == 200
    card = response.json()
    assert card["history"][0]["to_stage"]["code"] == "signing"
    assert [t["to_stage"]["code"] for t in card["allowed_transitions"]] == ["materials_transfer"]
    assert {s["kind"] for s in card["signals"]} == {"stage_overdue", "missing_document"}


async def test_foreign_interaction_is_not_found(client: AsyncClient) -> None:
    foreign = await find(client, MIKHAIL_KAM, search="УрФУ")

    card = await client.get(f"/api/v1/interactions/{foreign['id']}", headers=as_user(ANNA_KAM))
    transition = await client.post(
        f"/api/v1/interactions/{foreign['id']}/transitions",
        json={"to_stage_id": foreign["stage"]["id"], "comment": "x", "expected_version": 1},
        headers=as_user(ANNA_KAM),
    )

    assert (card.status_code, transition.status_code) == (404, 404)


async def test_transition_moves_stage_and_closes_overdue(
    client: AsyncClient, session: AsyncSession
) -> None:
    item = await find(client, ANNA_KAM, stage_code="signing")
    target = await stage_id(client, "materials_transfer")
    # Выход с «Подписания» закрывается договором, поэтому сначала документ.
    attachment = await upload_pdf(client, ANNA_KAM, item["id"], "signed_contract")

    response = await client.post(
        f"/api/v1/interactions/{item['id']}/transitions",
        json={
            "to_stage_id": target,
            "comment": "Договор подписан",
            "expected_version": 1,
            "attachment_ids": [attachment["id"]],
        },
        headers=as_user(ANNA_KAM),
    )

    assert response.status_code == 201
    result = response.json()
    assert result["transition"]["comment"] == "Договор подписан"
    card = result["interaction"]
    assert (card["stage"]["code"], card["version"], card["days_on_stage"]) == (
        "materials_transfer",
        2,
        0,
    )
    assert card["signals"] == []
    audit = await session.scalar(select(AuditLog).where(AuditLog.entity_id == item["id"]))
    assert audit is not None
    assert audit.action == "interaction.transition"


async def test_transition_requires_comment(client: AsyncClient) -> None:
    item = await find(client, ANNA_KAM, stage_code="signing")
    target = await stage_id(client, "materials_transfer")

    response = await client.post(
        f"/api/v1/interactions/{item['id']}/transitions",
        json={"to_stage_id": target, "comment": "   ", "expected_version": 1},
        headers=as_user(ANNA_KAM),
    )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "WF_COMMENT_REQUIRED"
    assert body["errors"] == [{"field": "comment", "message": "Обязательное поле"}]


async def test_stale_version_is_conflict(client: AsyncClient) -> None:
    item = await find(client, ANNA_KAM, stage_code="signing")
    target = await stage_id(client, "materials_transfer")

    response = await client.post(
        f"/api/v1/interactions/{item['id']}/transitions",
        json={"to_stage_id": target, "comment": "Повтор", "expected_version": 7},
        headers=as_user(ANNA_KAM),
    )

    assert response.status_code == 409
    assert response.json()["code"] == "INTERACTION_VERSION_CONFLICT"


async def test_skipping_stages_is_not_allowed(client: AsyncClient) -> None:
    item = await find(client, ANNA_KAM, stage_code="signing")
    target = await stage_id(client, "classes")

    response = await client.post(
        f"/api/v1/interactions/{item['id']}/transitions",
        json={"to_stage_id": target, "comment": "Сразу к занятиям", "expected_version": 1},
        headers=as_user(ANNA_KAM),
    )

    assert response.status_code == 409
    assert response.json()["code"] == "WF_TRANSITION_NOT_ALLOWED"


async def test_final_stage_offers_no_transitions(
    client: AsyncClient, session: AsyncSession
) -> None:
    item = await find(client, ANNA_KAM, search="КФУ")
    final_stage = await session.scalar(
        select(Stage.id).where(Stage.code == "stage_control").limit(1)
    )
    await session.execute(
        update(Interaction).where(Interaction.id == item["id"]).values(current_stage_id=final_stage)
    )
    await session.commit()

    card = await client.get(f"/api/v1/interactions/{item['id']}", headers=as_user(ANNA_KAM))

    assert card.json()["allowed_transitions"] == []


@pytest.mark.parametrize(
    "statement", ["UPDATE transition SET comment = 'правка'", "DELETE FROM transition"]
)
async def test_transition_history_is_append_only(
    connection: AsyncConnection, statement: str
) -> None:
    with pytest.raises(DBAPIError, match="только дописывается"):
        async with connection.begin_nested():
            await connection.execute(text(statement))


@pytest.mark.parametrize(
    "statement", ["UPDATE audit_log SET action = 'правка'", "DELETE FROM audit_log"]
)
async def test_audit_log_is_append_only(connection: AsyncConnection, statement: str) -> None:
    # Построчный триггер срабатывает только на существующих строках, поэтому сначала пишем запись.
    await connection.execute(
        text("INSERT INTO audit_log (action, entity_kind) VALUES ('test', 'test')")
    )
    with pytest.raises(DBAPIError, match="только дописывается"):
        async with connection.begin_nested():
            await connection.execute(text(statement))
