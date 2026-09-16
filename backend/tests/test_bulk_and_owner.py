"""Групповой переход и смена ответственного."""

import uuid
from typing import Any

from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog
from app.modules.interactions.models import AssignmentChange
from app.modules.workflow.models import StageTransitionRule
from tests.api import find, stage_id, user_id
from tests.users import ALINA_ADMIN, ANNA_KAM, MIKHAIL_KAM, ROMAN_MANAGER, as_user

BULK_TRANSITIONS = "/api/v1/interactions/bulk-transitions"
BULK_OWNER = "/api/v1/interactions/bulk-owner"


def result_for(body: dict[str, Any], interaction_id: str) -> dict[str, Any]:
    return next(item for item in body["results"] if item["interaction_id"] == interaction_id)


async def test_bulk_transition_gives_each_record_its_own_result(client: AsyncClient) -> None:
    signing = await find(client, ANNA_KAM, stage_code="signing")
    classes = await find(client, ANNA_KAM, stage_code="classes")
    foreign = await find(client, MIKHAIL_KAM, search="УрФУ")

    response = await client.post(
        BULK_TRANSITIONS,
        json={
            "interaction_ids": [signing["id"], classes["id"], foreign["id"]],
            "to_stage_code": "materials_transfer",
            "comment": "Договоры подписаны",
        },
        headers=as_user(ANNA_KAM),
    )

    assert response.status_code == 200
    body = response.json()
    assert (body["succeeded"], body["failed"]) == (1, 2)
    assert result_for(body, signing["id"])["version"] == 2
    # «Ведение занятий» без bulk_allowed и чужая запись — отказы, но не мешают остальным.
    assert result_for(body, classes["id"])["code"] == "WF_TRANSITION_NOT_ALLOWED"
    assert result_for(body, foreign["id"])["code"] == "NOT_FOUND"

    card = (
        await client.get(f"/api/v1/interactions/{signing['id']}", headers=as_user(ANNA_KAM))
    ).json()
    assert card["stage"]["code"] == "materials_transfer"
    assert card["history"][0]["source"] == "bulk"


async def test_bulk_transition_requires_comment(client: AsyncClient) -> None:
    signing = await find(client, ANNA_KAM, stage_code="signing")

    response = await client.post(
        BULK_TRANSITIONS,
        json={
            "interaction_ids": [signing["id"]],
            "to_stage_code": "materials_transfer",
            "comment": "   ",
        },
        headers=as_user(ANNA_KAM),
    )

    body = response.json()
    assert (body["succeeded"], body["failed"]) == (0, 1)
    assert body["results"][0]["code"] == "WF_COMMENT_REQUIRED"


async def test_bulk_transition_with_required_document_is_sent_to_card(
    client: AsyncClient, session: AsyncSession
) -> None:
    signing = await find(client, ANNA_KAM, stage_code="signing")
    target = await stage_id(client, "materials_transfer")
    await session.execute(
        update(StageTransitionRule)
        .where(StageTransitionRule.to_stage_id == uuid.UUID(target))
        .values(requires_attachment=True)
    )
    await session.commit()

    response = await client.post(
        BULK_TRANSITIONS,
        json={
            "interaction_ids": [signing["id"]],
            "to_stage_code": "materials_transfer",
            "comment": "Договор подписан",
        },
        headers=as_user(ANNA_KAM),
    )

    assert response.json()["results"][0]["code"] == "WF_ATTACHMENT_REQUIRED"


async def test_unknown_stage_code_is_refused(client: AsyncClient) -> None:
    signing = await find(client, ANNA_KAM, stage_code="signing")

    response = await client.post(
        BULK_TRANSITIONS,
        json={
            "interaction_ids": [signing["id"]],
            "to_stage_code": "no_such_stage",
            "comment": "Проверка",
        },
        headers=as_user(ANNA_KAM),
    )

    assert response.json()["results"][0]["code"] == "WF_TRANSITION_NOT_ALLOWED"


async def test_manager_changes_owner_inside_team(
    client: AsyncClient, session: AsyncSession
) -> None:
    item = await find(client, ANNA_KAM, stage_code="signing")
    mikhail = await user_id(session, MIKHAIL_KAM)

    response = await client.put(
        f"/api/v1/interactions/{item['id']}/owner",
        json={"owner_id": str(mikhail), "reason": "Анна в отпуске", "expected_version": 1},
        headers=as_user(ROMAN_MANAGER),
    )

    assert response.status_code == 200
    card = response.json()
    assert (card["owner"]["full_name"], card["version"]) == ("Михаил Волков", 2)
    change = await session.scalar(
        select(AssignmentChange).where(AssignmentChange.interaction_id == item["id"])
    )
    assert change is not None
    assert (change.to_user_id, change.reason) == (mikhail, "Анна в отпуске")
    audit = await session.scalar(
        select(AuditLog).where(
            AuditLog.entity_id == item["id"], AuditLog.action == "interaction.owner_change"
        )
    )
    assert audit is not None


async def test_kam_cannot_change_owner(client: AsyncClient, session: AsyncSession) -> None:
    item = await find(client, ANNA_KAM, stage_code="signing")
    mikhail = await user_id(session, MIKHAIL_KAM)

    response = await client.put(
        f"/api/v1/interactions/{item['id']}/owner",
        json={"owner_id": str(mikhail), "reason": "Передаю коллеге", "expected_version": 1},
        headers=as_user(ANNA_KAM),
    )

    assert response.status_code == 403
    assert response.json()["code"] == "AUTH_FORBIDDEN"


async def test_manager_cannot_assign_outside_team(
    client: AsyncClient, session: AsyncSession
) -> None:
    item = await find(client, ANNA_KAM, stage_code="signing")
    outside_team = await user_id(session, ALINA_ADMIN)

    response = await client.put(
        f"/api/v1/interactions/{item['id']}/owner",
        json={"owner_id": str(outside_team), "reason": "Пусть ведёт админ", "expected_version": 1},
        headers=as_user(ROMAN_MANAGER),
    )

    assert response.status_code == 403
    assert response.json()["code"] == "AUTH_FORBIDDEN"


async def test_owner_change_checks_version(client: AsyncClient, session: AsyncSession) -> None:
    item = await find(client, ANNA_KAM, stage_code="signing")
    mikhail = await user_id(session, MIKHAIL_KAM)

    response = await client.put(
        f"/api/v1/interactions/{item['id']}/owner",
        json={"owner_id": str(mikhail), "reason": "Повтор", "expected_version": 7},
        headers=as_user(ROMAN_MANAGER),
    )

    assert response.status_code == 409
    assert response.json()["code"] == "INTERACTION_VERSION_CONFLICT"


async def test_unknown_user_cannot_be_assigned(client: AsyncClient) -> None:
    item = await find(client, ANNA_KAM, stage_code="signing")

    response = await client.put(
        f"/api/v1/interactions/{item['id']}/owner",
        json={
            "owner_id": "00000000-0000-4000-8000-000000000000",
            "reason": "Опечатка",
            "expected_version": 1,
        },
        headers=as_user(ALINA_ADMIN),
    )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["errors"] == [{"field": "owner_id", "message": "Неизвестный сотрудник"}]


async def test_admin_transfers_several_interactions(
    client: AsyncClient, session: AsyncSession
) -> None:
    anna = (await client.get("/api/v1/interactions", headers=as_user(ANNA_KAM))).json()["items"]
    mikhail = await user_id(session, MIKHAIL_KAM)

    response = await client.post(
        BULK_OWNER,
        json={
            "interaction_ids": [item["id"] for item in anna[:2]],
            "owner_id": str(mikhail),
            "reason": "Перераспределение нагрузки",
        },
        headers=as_user(ALINA_ADMIN),
    )

    assert response.json()["succeeded"] == 2
    left = await client.get("/api/v1/interactions", headers=as_user(ANNA_KAM))
    received = await client.get("/api/v1/interactions", headers=as_user(MIKHAIL_KAM))
    assert (left.json()["total"], received.json()["total"]) == (2, 4)


async def test_kam_cannot_transfer_in_bulk(client: AsyncClient, session: AsyncSession) -> None:
    item = await find(client, ANNA_KAM, stage_code="signing")
    mikhail = await user_id(session, MIKHAIL_KAM)

    response = await client.post(
        BULK_OWNER,
        json={
            "interaction_ids": [item["id"]],
            "owner_id": str(mikhail),
            "reason": "Передаю коллеге",
        },
        headers=as_user(ANNA_KAM),
    )

    assert response.status_code == 403
    assert response.json()["code"] == "AUTH_FORBIDDEN"
