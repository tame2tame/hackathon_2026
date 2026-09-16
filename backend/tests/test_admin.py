"""Администрирование: правила доступа, шифрование контактов, аудит и каталоги."""

from typing import Any

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalogs.models import ContactPerson, University
from tests.api import user_id
from tests.users import ALINA_ADMIN, ANNA_KAM, ROMAN_MANAGER, as_user

ADMIN = "/api/v1/admin"


async def university_by(session: AsyncSession, short_name: str) -> University:
    university = await session.scalar(select(University).where(University.short_name == short_name))
    assert university is not None
    return university


async def deny_rule(client: AsyncClient, email: str, university_id: str) -> dict[str, Any]:
    response = await client.post(
        f"{ADMIN}/access-rules",
        json={
            "subject_user_id": email,
            "effect": "deny",
            "scope_kind": "university",
            "scope_id": university_id,
            "comment": "Вуз ведёт другая команда",
        },
        headers=as_user(ALINA_ADMIN),
    )
    assert response.status_code == 201, response.text
    rule: dict[str, Any] = response.json()
    return rule


async def test_admin_section_is_closed_for_others(client: AsyncClient) -> None:
    kam = await client.get(f"{ADMIN}/users", headers=as_user(ANNA_KAM))
    manager = await client.get(f"{ADMIN}/users", headers=as_user(ROMAN_MANAGER))
    admin = await client.get(f"{ADMIN}/users", headers=as_user(ALINA_ADMIN))

    assert (kam.status_code, manager.status_code) == (403, 403)
    assert admin.status_code == 200
    assert len(admin.json()) == 4


async def test_deny_rule_hides_a_university_everywhere(
    client: AsyncClient, session: AsyncSession
) -> None:
    anna = await user_id(session, ANNA_KAM)
    mgtu = await university_by(session, "МГТУ")
    before = await client.get("/api/v1/interactions", headers=as_user(ANNA_KAM))
    assert before.json()["total"] == 4

    await deny_rule(client, str(anna), str(mgtu.id))

    interactions = await client.get("/api/v1/interactions", headers=as_user(ANNA_KAM))
    signals = await client.get("/api/v1/signals", headers=as_user(ANNA_KAM))
    report = await client.post(
        "/api/v1/reports", json={"format": "json"}, headers=as_user(ANNA_KAM)
    )

    assert interactions.json()["total"] == 3
    # Сигналы МГТУ тоже исчезают: правило работает в области видимости, а не в одном списке.
    assert all(
        item["interaction"]["university"]["short_name"] != "МГТУ"
        for item in signals.json()["items"]
    )
    assert report.json()["row_count"] == 3


async def test_rule_can_be_removed(client: AsyncClient, session: AsyncSession) -> None:
    anna = await user_id(session, ANNA_KAM)
    mgtu = await university_by(session, "МГТУ")
    rule = await deny_rule(client, str(anna), str(mgtu.id))

    removed = await client.delete(
        f"{ADMIN}/access-rules/{rule['id']}", headers=as_user(ALINA_ADMIN)
    )
    after = await client.get("/api/v1/interactions", headers=as_user(ANNA_KAM))

    assert removed.status_code == 204
    assert after.json()["total"] == 4


async def test_rule_needs_exactly_one_subject(client: AsyncClient, session: AsyncSession) -> None:
    mgtu = await university_by(session, "МГТУ")

    response = await client.post(
        f"{ADMIN}/access-rules",
        json={"effect": "deny", "scope_kind": "university", "scope_id": str(mgtu.id)},
        headers=as_user(ALINA_ADMIN),
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


async def test_contact_is_stored_encrypted(client: AsyncClient, session: AsyncSession) -> None:
    mgtu = await university_by(session, "МГТУ")

    created = await client.post(
        f"/api/v1/universities/{mgtu.id}/contacts",
        json={
            "full_name": "Ирина Петрова",
            "position": "Проректор",
            "email": "irina@example.com",
            "phone": "+7 999 000-00-00",
        },
        headers=as_user(ANNA_KAM),
    )

    assert created.status_code == 201
    assert created.json()["email"] == "irina@example.com"
    stored = await session.scalar(
        select(ContactPerson).where(ContactPerson.full_name == "Ирина Петрова")
    )
    assert stored is not None
    assert stored.email_enc is not None
    # В базе лежит шифротекст, а не адрес.
    assert b"irina@example.com" not in stored.email_enc


async def test_viewing_contacts_is_written_to_the_audit(
    client: AsyncClient, session: AsyncSession
) -> None:
    mgtu = await university_by(session, "МГТУ")

    await client.get(f"/api/v1/universities/{mgtu.id}/contacts", headers=as_user(ANNA_KAM))
    audit = await client.get(
        f"{ADMIN}/audit", params={"action": "contact.viewed"}, headers=as_user(ALINA_ADMIN)
    )

    assert audit.status_code == 200
    entries = audit.json()
    assert entries
    assert entries[0]["entity_id"] == str(mgtu.id)


async def test_user_change_keeps_before_and_after(
    client: AsyncClient, session: AsyncSession
) -> None:
    mikhail = await user_id(session, "mikhail.volkov@example.com")

    response = await client.patch(
        f"{ADMIN}/users/{mikhail}", json={"is_active": False}, headers=as_user(ALINA_ADMIN)
    )
    audit = await client.get(
        f"{ADMIN}/audit", params={"action": "admin.user_changed"}, headers=as_user(ALINA_ADMIN)
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    entry = audit.json()[0]
    assert entry["before"]["is_active"] is True
    assert entry["after"]["is_active"] is False


async def test_catalog_item_is_archived_not_deleted(
    client: AsyncClient, session: AsyncSession
) -> None:
    created = await client.post(
        f"{ADMIN}/catalogs/vendors", json={"name": "Новый вендор"}, headers=as_user(ALINA_ADMIN)
    )
    assert created.status_code == 201
    item = created.json()

    archived = await client.post(
        f"{ADMIN}/catalogs/vendors/{item['id']}/archive", headers=as_user(ALINA_ADMIN)
    )

    assert archived.status_code == 200
    assert archived.json()["archived_at"] is not None


async def test_setting_is_saved_with_audit(client: AsyncClient) -> None:
    response = await client.put(
        f"{ADMIN}/settings/radar_thresholds",
        json={"value": {"inactivity_low_days": 14}},
        headers=as_user(ALINA_ADMIN),
    )
    settings = await client.get(f"{ADMIN}/settings", headers=as_user(ALINA_ADMIN))

    assert response.status_code == 200
    assert response.json()["value"] == {"inactivity_low_days": 14}
    assert any(item["key"] == "radar_thresholds" for item in settings.json())


async def test_team_can_be_created(client: AsyncClient) -> None:
    response = await client.post(
        f"{ADMIN}/teams", json={"name": "Сибирь и Дальний Восток"}, headers=as_user(ALINA_ADMIN)
    )
    teams = await client.get(f"{ADMIN}/teams", headers=as_user(ALINA_ADMIN))

    assert response.status_code == 201
    assert "Сибирь и Дальний Восток" in {team["name"] for team in teams.json()}
