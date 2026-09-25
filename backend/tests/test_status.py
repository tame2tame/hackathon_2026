"""Состояние записи: пауза, завершение, отмена и возврат в работу."""

import uuid
from typing import Any

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.interactions.models import Interaction
from app.modules.workflow.models import WorkflowVersion
from tests.api import find, stage_id
from tests.test_workflow_editor import draft_without, publish
from tests.users import ANNA_KAM, MIKHAIL_KAM, ROMAN_MANAGER, as_user

INTERACTIONS = "/api/v1/interactions"


async def set_status(
    client: AsyncClient, item: dict[str, Any], status: str, email: str = ANNA_KAM, **extra: Any
) -> Any:
    return await client.put(
        f"{INTERACTIONS}/{item['id']}/status",
        json={"status": status, "expected_version": item["version"], **extra},
        headers=as_user(email),
    )


async def test_paused_record_loses_signals_and_refuses_transitions(client: AsyncClient) -> None:
    mgtu = await find(client, ANNA_KAM, stage_code="signing")
    assert {signal["kind"] for signal in mgtu["open_signals"]} == {
        "stage_overdue",
        "missing_document",
    }

    paused = await set_status(client, mgtu, "paused", reason="Вуз ушёл на каникулы")
    card = paused.json()
    moved = await client.post(
        f"{INTERACTIONS}/{mgtu['id']}/transitions",
        json={
            "to_stage_id": await stage_id(client, "materials_transfer"),
            "comment": "Пробуем двигать",
            "expected_version": card["version"],
        },
        headers=as_user(ANNA_KAM),
    )

    assert paused.status_code == 200, paused.text
    assert (card["status"], card["version"]) == ("paused", mgtu["version"] + 1)
    # Приостановленная запись не висит в радаре и не принимает переходы.
    assert card["signals"] == []
    assert moved.status_code == 409
    assert moved.json()["code"] == "WF_TRANSITION_NOT_ALLOWED"


async def test_reason_is_required_for_pause_and_cancel(client: AsyncClient) -> None:
    kfu = await find(client, ANNA_KAM, search="КФУ")

    silent = await set_status(client, kfu, "cancelled")
    told = await set_status(client, kfu, "cancelled", reason="Вуз отказался от программы")

    assert silent.status_code == 422
    assert silent.json()["errors"] == [{"field": "reason", "message": "Обязательное поле"}]
    assert told.json()["status"] == "cancelled"


async def test_cancelled_record_leaves_the_list_but_keeps_its_page(client: AsyncClient) -> None:
    kfu = await find(client, ANNA_KAM, search="КФУ")
    await set_status(client, kfu, "cancelled", reason="Вуз отказался")

    listed = await client.get(INTERACTIONS, headers=as_user(ANNA_KAM))
    filtered = await client.get(
        INTERACTIONS, params={"status": "cancelled"}, headers=as_user(ANNA_KAM)
    )
    card = await client.get(f"{INTERACTIONS}/{kfu['id']}", headers=as_user(ANNA_KAM))

    assert kfu["id"] not in {item["id"] for item in listed.json()["items"]}
    assert [item["id"] for item in filtered.json()["items"]] == [kfu["id"]]
    assert card.status_code == 200


async def test_completed_record_can_be_reopened(client: AsyncClient) -> None:
    itmo = await find(client, ANNA_KAM, stage_code="classes")

    completed = await set_status(client, itmo, "completed")
    paused = await set_status(client, completed.json(), "paused", reason="Передумали")
    reopened = await set_status(client, completed.json(), "active")

    assert completed.json()["status"] == "completed"
    # Из завершённой сразу в паузу нельзя: сначала возвращают в работу.
    assert paused.status_code == 409
    assert reopened.json()["status"] == "active"


async def test_restoring_is_refused_when_the_pair_is_taken(client: AsyncClient) -> None:
    ngu = await find(client, MIKHAIL_KAM, search="НГУ")
    await set_status(client, ngu, "cancelled", MIKHAIL_KAM, reason="Отложили")
    again = await client.post(
        INTERACTIONS,
        json={
            "group_id": ngu["group"]["id"],
            "university_id": ngu["university"]["id"],
            "program_id": ngu["program"]["id"],
            "product_id": ngu["product"]["id"],
        },
        headers=as_user(MIKHAIL_KAM),
    )
    assert again.status_code == 201, again.text

    restored = await set_status(
        client, {"id": ngu["id"], "version": ngu["version"] + 1}, "active", MIKHAIL_KAM
    )

    assert restored.status_code == 409
    assert restored.json()["code"] == "INTERACTION_DUPLICATE"


async def test_status_change_by_a_manager_is_seen_by_the_owner(client: AsyncClient) -> None:
    mgtu = await find(client, ANNA_KAM, stage_code="signing")

    response = await set_status(
        client, mgtu, "paused", ROMAN_MANAGER, reason="Ждём решения ректората"
    )
    feed = await client.get("/api/v1/notifications", headers=as_user(ANNA_KAM))
    stale = await set_status(client, mgtu, "completed")

    assert response.status_code == 200, response.text
    [item] = feed.json()["items"]
    assert item["title"] == "Запись приостановлена: «МГТУ — DevOps-инженерия»"
    assert item["body"].endswith("Причина: Ждём решения ректората")
    # Версия выросла — старая карточка больше не подходит.
    assert stale.status_code == 409
    assert stale.json()["code"] == "INTERACTION_VERSION_CONFLICT"


async def test_foreign_record_status_is_not_found(client: AsyncClient) -> None:
    foreign = await find(client, MIKHAIL_KAM, search="УрФУ")

    response = await set_status(client, foreign, "paused", ANNA_KAM, reason="Хочу")

    assert response.status_code == 404


async def test_restored_record_follows_the_current_process(
    client: AsyncClient, session: AsyncSession
) -> None:
    kfu = await find(client, ANNA_KAM, search="КФУ")
    cancelled = await set_status(client, kfu, "cancelled", reason="Заведено по ошибке")
    # Пока запись отменена, процесс меняют: её этап «Встреча» из схемы убирают.
    draft = await draft_without(client, session, {"meeting"})
    published = await publish(client, draft)

    restored = await set_status(client, cancelled.json(), "active")
    record = await session.get(Interaction, uuid.UUID(kfu["id"]))
    await session.refresh(record)
    scheme = await session.get(WorkflowVersion, record.workflow_version_id)

    assert published.status_code == 200, published.text
    assert restored.status_code == 200, restored.text
    # Запись не осталась на выведенной схеме: она на действующей и на соседнем этапе.
    assert scheme is not None
    assert scheme.status == "published"
    assert restored.json()["stage"]["code"] == "communication"
