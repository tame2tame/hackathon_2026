"""Группы контрагентов B2B и B2C: свои процессы, клиенты вне вузов и записи, заведённые вручную."""

import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog
from app.modules.catalogs.models import University
from app.modules.clients.models import Client
from app.modules.interactions.models import Interaction
from app.modules.radar.service import recompute_signals
from tests.api import user_id
from tests.users import ALINA_ADMIN, ANNA_KAM, MIKHAIL_KAM, ROMAN_MANAGER, as_user

GROUPS = "/api/v1/counterparty-groups"
CLIENTS = "/api/v1/clients"
INTERACTIONS = "/api/v1/interactions"


async def groups(client: AsyncClient) -> dict[str, dict[str, Any]]:
    response = await client.get(GROUPS, headers=as_user(ANNA_KAM))
    assert response.status_code == 200
    return {group["code"]: group for group in response.json()}


async def catalog_id(client: AsyncClient, path: str, name: str) -> str:
    items = (await client.get(f"/api/v1/{path}", headers=as_user(ANNA_KAM))).json()
    return str(next(item["id"] for item in items if item["name"] == name))


async def devops(client: AsyncClient) -> dict[str, str]:
    """Продуктозависимая программа v0 и её продукт."""
    return {
        "program_id": await catalog_id(client, "programs", "DevOps-инженерия"),
        "product_id": await catalog_id(client, "products", "Базис"),
    }


async def new_client(client: AsyncClient, user: str = ANNA_KAM, **fields: Any) -> dict[str, Any]:
    body = {"kind": "person", "name": "Петров Иван", "email": "ivan.petrov@example.com", **fields}
    response = await client.post(CLIENTS, json=body, headers=as_user(user))
    assert response.status_code == 201, response.text
    created: dict[str, Any] = response.json()
    return created


async def b2c_record(client: AsyncClient, email: str = ANNA_KAM) -> dict[str, Any]:
    person = await new_client(client, email)
    response = await client.post(
        INTERACTIONS,
        json={
            "group_id": (await groups(client))["individuals"]["id"],
            "client_id": person["id"],
            **await devops(client),
            "comment": "Позвонил сам, хочет на курс DevOps",
        },
        headers=as_user(email),
    )
    assert response.status_code == 201, response.text
    record: dict[str, Any] = response.json()
    return record


async def test_each_group_has_its_own_process(client: AsyncClient) -> None:
    by_code = await groups(client)

    b2b, b2c = by_code["universities"], by_code["individuals"]
    workflow = await client.get(
        f"/api/v1/workflows/{b2c['workflow_template_id']}", headers=as_user(ANNA_KAM)
    )

    assert b2b["workflow_template_id"] != b2c["workflow_template_id"]
    body = workflow.json()
    codes = [stage["code"] for stage in body["stages"]]
    assert codes[0] == "application"
    assert codes[-1] == "completed"
    by_id = {stage["id"]: stage["code"] for stage in body["stages"]}
    pairs = {
        (by_id[rule["from_stage_id"]], by_id[rule["to_stage_id"]]) for rule in body["transitions"]
    }
    assert ("application", "consultation") in pairs
    assert ("consultation", "application") in pairs


async def test_workflows_list_shows_the_groups_they_serve(client: AsyncClient) -> None:
    response = await client.get("/api/v1/workflows", headers=as_user(ROMAN_MANAGER))

    assert response.status_code == 200
    served = {
        group["code"]: workflow for workflow in response.json() for group in workflow["groups"]
    }
    assert served["universities"]["is_default"] is True
    assert served["individuals"]["is_default"] is False
    assert served["individuals"]["published_version_id"] is not None


async def test_person_contacts_are_encrypted_and_viewing_is_audited(
    client: AsyncClient, session: AsyncSession
) -> None:
    person = await new_client(client)

    stored = await session.get(Client, person["id"])
    card = await client.get(f"{CLIENTS}/{person['id']}", headers=as_user(ANNA_KAM))

    assert stored is not None
    assert stored.email_enc is not None
    assert b"ivan.petrov" not in stored.email_enc
    assert card.json()["email"] == "ivan.petrov@example.com"
    viewed = await session.scalar(
        select(AuditLog).where(AuditLog.action == "client.viewed", AuditLog.entity_id == stored.id)
    )
    assert viewed is not None


async def test_people_are_private_but_organizations_are_shared(client: AsyncClient) -> None:
    person = await new_client(client)
    company = await new_client(
        client, kind="organization", name="ООО «Проверочная»", inn="0012345678", email=None
    )

    foreign_person = await client.get(f"{CLIENTS}/{person['id']}", headers=as_user(MIKHAIL_KAM))
    shared_company = await client.get(f"{CLIENTS}/{company['id']}", headers=as_user(MIKHAIL_KAM))
    listed = await client.get(CLIENTS, headers=as_user(MIKHAIL_KAM))

    assert foreign_person.status_code == 404
    assert shared_company.status_code == 200
    assert [item["name"] for item in listed.json()["items"]] == ["ООО «Проверочная»"]


async def test_client_details_are_validated(client: AsyncClient) -> None:
    await new_client(client, kind="organization", name="ООО «Первая»", inn="0011111111", email=None)

    same_inn = await client.post(
        CLIENTS,
        json={"kind": "organization", "name": "ООО «Вторая»", "inn": "0011111111"},
        headers=as_user(ANNA_KAM),
    )
    person_inn = await client.post(
        CLIENTS,
        json={"kind": "person", "name": "Сидорова Анна", "inn": "001234567890"},
        headers=as_user(ANNA_KAM),
    )

    assert same_inn.status_code == 422
    assert same_inn.json()["errors"] == [{"field": "inn", "message": "ИНН уже занят"}]
    assert person_inn.status_code == 422


async def test_kam_starts_a_b2c_record_on_its_own_process(client: AsyncClient) -> None:
    record = await b2c_record(client)
    by_code = await groups(client)

    b2c = await client.get(
        INTERACTIONS, params={"group_id": by_code["individuals"]["id"]}, headers=as_user(ANNA_KAM)
    )
    b2b = await client.get(
        INTERACTIONS, params={"group_id": by_code["universities"]["id"]}, headers=as_user(ANNA_KAM)
    )

    assert record["group"]["code"] == "individuals"
    assert record["stage"]["code"] == "application"
    assert record["counterparty"] == {
        "kind": "person",
        "id": record["client"]["id"],
        "name": "Петров Иван",
        "short_name": "Петров Иван",
    }
    assert record["university"] is None
    assert [step["comment"] for step in record["history"]] == ["Позвонил сам, хочет на курс DevOps"]
    assert [item["id"] for item in b2c.json()["items"]] == [record["id"]]
    assert b2b.json()["total"] == 4


async def test_b2c_record_moves_only_along_its_process(client: AsyncClient) -> None:
    record = await b2c_record(client)
    [forward] = record["allowed_transitions"]
    workflow = (
        await client.get(
            f"/api/v1/workflows/{(await groups(client))['individuals']['workflow_template_id']}",
            headers=as_user(ANNA_KAM),
        )
    ).json()
    training = next(stage for stage in workflow["stages"] if stage["code"] == "training")

    jump = await client.post(
        f"{INTERACTIONS}/{record['id']}/transitions",
        json={"to_stage_id": training["id"], "comment": "Сразу учиться", "expected_version": 1},
        headers=as_user(ANNA_KAM),
    )
    step = await client.post(
        f"{INTERACTIONS}/{record['id']}/transitions",
        json={
            "to_stage_id": forward["to_stage"]["id"],
            "comment": "Созвонились",
            "expected_version": 1,
        },
        headers=as_user(ANNA_KAM),
    )

    assert forward["to_stage"]["code"] == "consultation"
    assert jump.status_code == 409
    assert jump.json()["code"] == "WF_TRANSITION_NOT_ALLOWED"
    assert step.status_code == 201, step.text


async def test_same_counterparty_program_and_product_is_one_record(client: AsyncClient) -> None:
    record = await b2c_record(client)

    duplicate = await client.post(
        INTERACTIONS,
        json={
            "group_id": record["group"]["id"],
            "client_id": record["client"]["id"],
            **await devops(client),
        },
        headers=as_user(ANNA_KAM),
    )

    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "INTERACTION_DUPLICATE"


async def test_counterparty_and_product_are_checked(
    client: AsyncClient, session: AsyncSession
) -> None:
    group_id = (await groups(client))["universities"]["id"]
    university = await session.scalar(select(University).where(University.short_name == "НГУ"))
    assert university is not None
    person = await new_client(client)
    base = {"group_id": group_id, **await devops(client)}

    both = await client.post(
        INTERACTIONS,
        json={**base, "university_id": str(university.id), "client_id": person["id"]},
        headers=as_user(ANNA_KAM),
    )
    neither = await client.post(INTERACTIONS, json=base, headers=as_user(ANNA_KAM))
    without_product = await client.post(
        INTERACTIONS,
        json={**base, "university_id": str(university.id), "product_id": None},
        headers=as_user(ANNA_KAM),
    )
    foreign_product = await client.post(
        INTERACTIONS,
        json={
            **base,
            "university_id": str(university.id),
            "product_id": await catalog_id(client, "products", "Loginom"),
        },
        headers=as_user(ANNA_KAM),
    )
    # У НГУ эту связку уже ведёт Михаил: запись одна на вуз, программу и продукт.
    taken = await client.post(
        INTERACTIONS, json={**base, "university_id": str(university.id)}, headers=as_user(ANNA_KAM)
    )

    assert (both.status_code, neither.status_code) == (422, 422)
    assert without_product.json()["errors"][0]["field"] == "product_id"
    assert foreign_product.json()["errors"][0]["field"] == "product_id"
    assert taken.status_code == 409


async def test_manual_university_record_starts_at_contact_search(
    client: AsyncClient, session: AsyncSession
) -> None:
    university = await session.scalar(select(University).where(University.short_name == "НГУ"))
    assert university is not None

    response = await client.post(
        INTERACTIONS,
        json={
            "group_id": (await groups(client))["universities"]["id"],
            "university_id": str(university.id),
            "program_id": await catalog_id(client, "programs", "Анализ данных"),
            "product_id": await catalog_id(client, "products", "Loginom"),
        },
        headers=as_user(ANNA_KAM),
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["stage"]["code"] == "contact_search"
    assert body["counterparty"]["kind"] == "university"
    assert body["counterparty"]["short_name"] == "НГУ"
    assert body["owner"]["full_name"] == "Анна Смирнова"


async def test_only_a_manager_assigns_someone_else(
    client: AsyncClient, session: AsyncSession
) -> None:
    anna = await user_id(session, ANNA_KAM)
    mikhail = await user_id(session, MIKHAIL_KAM)
    # Клиента завела Анна: его видит и она, и руководитель её команды.
    person = await new_client(client, ANNA_KAM)
    payload = {
        "group_id": (await groups(client))["individuals"]["id"],
        "client_id": person["id"],
        **await devops(client),
    }

    by_kam = await client.post(
        INTERACTIONS, json={**payload, "owner_id": str(mikhail)}, headers=as_user(ANNA_KAM)
    )
    by_manager = await client.post(
        INTERACTIONS, json={**payload, "owner_id": str(anna)}, headers=as_user(ROMAN_MANAGER)
    )

    assert by_kam.status_code == 403
    assert by_manager.status_code == 201, by_manager.text
    assert by_manager.json()["owner"]["full_name"] == "Анна Смирнова"


async def test_access_rule_by_group_hides_its_records(
    client: AsyncClient, session: AsyncSession
) -> None:
    record = await b2c_record(client)
    anna = await user_id(session, ANNA_KAM)

    rule = await client.post(
        "/api/v1/admin/access-rules",
        json={
            "subject_user_id": str(anna),
            "effect": "deny",
            "scope_kind": "group",
            "scope_id": record["group"]["id"],
            "comment": "Частных лиц ведёт другая команда",
        },
        headers=as_user(ALINA_ADMIN),
    )
    card = await client.get(f"{INTERACTIONS}/{record['id']}", headers=as_user(ANNA_KAM))
    listed = await client.get(INTERACTIONS, headers=as_user(ANNA_KAM))

    assert rule.status_code == 201, rule.text
    assert card.status_code == 404
    assert listed.json()["total"] == 4


async def test_report_names_the_group_and_the_counterparty(client: AsyncClient) -> None:
    await b2c_record(client)

    job = await client.post(
        "/api/v1/reports",
        json={"format": "json", "columns": ["group", "counterparty", "university", "product"]},
        headers=as_user(ANNA_KAM),
    )
    file = await client.get(f"/api/v1/reports/{job.json()['id']}/file", headers=as_user(ANNA_KAM))

    rows = json.loads(file.content)
    assert {
        "Группа": "Частные лица (B2C)",
        "Контрагент": "Петров Иван",
        "Вуз": "",
        "Продукт": "Базис",
    } in rows


async def test_radar_uses_the_norms_of_the_group_process(
    client: AsyncClient, session: AsyncSession
) -> None:
    record = await b2c_record(client)
    now = datetime.now(UTC)
    await session.execute(
        update(Interaction)
        .where(Interaction.id == record["id"])
        .values(stage_entered_at=now - timedelta(days=8), last_activity_at=now)
    )
    await recompute_signals(session, [record["id"]], now)
    await session.commit()

    card = (await client.get(f"{INTERACTIONS}/{record['id']}", headers=as_user(ANNA_KAM))).json()

    [overdue] = card["signals"]
    assert overdue["kind"] == "stage_overdue"
    # Норма «Заявки» — 3 дня: 8 дней больше двух норм.
    assert (overdue["evidence"]["norm_days"], overdue["severity"]) == (3, "high")


async def test_funnel_follows_the_group_process(client: AsyncClient) -> None:
    await b2c_record(client)
    b2c = (await groups(client))["individuals"]

    response = await client.get(
        "/api/v1/analytics/stats/funnel",
        params={"group_id": b2c["id"]},
        headers=as_user(ALINA_ADMIN),
    )

    body = response.json()
    assert body["labels"][0] == "Заявка"
    assert sum(body["values"]) == 1


async def test_norms_are_kept_per_process(client: AsyncClient) -> None:
    template_id = (await groups(client))["individuals"]["workflow_template_id"]

    norms = await client.get(f"/api/v1/workflows/{template_id}/norms", headers=as_user(ANNA_KAM))
    changed = await client.put(
        f"/api/v1/workflows/{template_id}/norms/application",
        json={"norm_days": 5},
        headers=as_user(ROMAN_MANAGER),
    )
    base = await client.get("/api/v1/workflows/default/norms", headers=as_user(ANNA_KAM))

    assert next(n for n in norms.json() if n["stage_code"] == "application")["norm_days"] == 3
    assert changed.json()["norm_days"] == 5
    assert "application" not in {norm["stage_code"] for norm in base.json()}


async def test_admin_manages_groups(client: AsyncClient) -> None:
    by_code = await groups(client)
    await b2c_record(client)
    payload = {
        "code": "companies",
        "name": "Корпоративные клиенты",
        "workflow_template_id": by_code["individuals"]["workflow_template_id"],
    }

    by_manager = await client.post(
        "/api/v1/admin/counterparty-groups", json=payload, headers=as_user(ROMAN_MANAGER)
    )
    created = await client.post(
        "/api/v1/admin/counterparty-groups", json=payload, headers=as_user(ALINA_ADMIN)
    )
    again = await client.post(
        "/api/v1/admin/counterparty-groups", json=payload, headers=as_user(ALINA_ADMIN)
    )
    busy_switch = await client.patch(
        f"/api/v1/admin/counterparty-groups/{by_code['individuals']['id']}",
        json={"workflow_template_id": by_code["universities"]["workflow_template_id"]},
        headers=as_user(ALINA_ADMIN),
    )
    busy_archive = await client.post(
        f"/api/v1/admin/counterparty-groups/{by_code['universities']['id']}/archive",
        headers=as_user(ALINA_ADMIN),
    )

    assert by_manager.status_code == 403
    assert created.status_code == 201, created.text
    assert "companies" in await groups(client)
    assert again.status_code == 422
    assert busy_switch.status_code == 422
    assert busy_archive.status_code == 422


async def test_deny_rule_for_a_university_keeps_client_records_visible(
    client: AsyncClient, session: AsyncSession
) -> None:
    record = await b2c_record(client)
    anna = await user_id(session, ANNA_KAM)
    mgtu = await session.scalar(select(University).where(University.short_name == "МГТУ"))
    assert mgtu is not None

    rule = await client.post(
        "/api/v1/admin/access-rules",
        json={
            "subject_user_id": str(anna),
            "effect": "deny",
            "scope_kind": "university",
            "scope_id": str(mgtu.id),
        },
        headers=as_user(ALINA_ADMIN),
    )
    listed = await client.get(INTERACTIONS, headers=as_user(ANNA_KAM))

    assert rule.status_code == 201, rule.text
    names = {item["counterparty"]["short_name"] for item in listed.json()["items"]}
    # Запрет по вузу убирает только его записи: у записи частного лица вуза нет.
    assert "МГТУ" not in names
    assert record["id"] in {item["id"] for item in listed.json()["items"]}


async def test_person_inn_cannot_hide_behind_an_organization(client: AsyncClient) -> None:
    response = await client.post(
        CLIENTS,
        json={"kind": "organization", "name": "ИП Кузнецов", "inn": "500100732259"},
        headers=as_user(ANNA_KAM),
    )

    assert response.status_code == 422
    assert "12 цифр" in response.json()["errors"][0]["message"]


async def test_organization_contacts_are_shown_only_to_those_who_work_with_it(
    client: AsyncClient, session: AsyncSession
) -> None:
    company = await new_client(
        client,
        ANNA_KAM,
        kind="organization",
        name="ООО «Контактная»",
        inn="0055555555",
        email="office@example.com",
    )

    mine = await client.get(f"{CLIENTS}/{company['id']}", headers=as_user(ANNA_KAM))
    foreign = await client.get(f"{CLIENTS}/{company['id']}", headers=as_user(MIKHAIL_KAM))

    assert mine.json()["email"] == "office@example.com"
    # Карточка видна, чтобы не плодить дубли, но контакты — персональные данные.
    assert foreign.status_code == 200
    assert foreign.json()["email"] is None
    viewed = await session.scalars(
        select(AuditLog).where(
            AuditLog.action == "client.viewed", AuditLog.entity_id == uuid.UUID(company["id"])
        )
    )
    assert len(list(viewed)) == 1
