"""Администрирование: правила доступа, шифрование контактов, аудит и каталоги."""

import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import _user_from_claims
from app.modules.catalogs.models import AppUser, ContactPerson, University
from tests.api import find, user_id
from tests.users import ALINA_ADMIN, ANNA_KAM, MIKHAIL_KAM, ROMAN_MANAGER, as_user

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


async def test_settings_show_defaults_until_saved(client: AsyncClient) -> None:
    response = await client.get(f"{ADMIN}/settings", headers=as_user(ALINA_ADMIN))

    radar = next(item for item in response.json() if item["key"] == "radar_thresholds")
    assert radar["is_default"] is True
    assert radar["updated_at"] is None
    assert radar["value"]["inactivity_low_days"] == 14


async def test_setting_is_saved_with_audit(client: AsyncClient) -> None:
    response = await client.put(
        f"{ADMIN}/settings/radar_thresholds",
        json={"value": {"inactivity_low_days": 10}},
        headers=as_user(ALINA_ADMIN),
    )
    audit = await client.get(
        f"{ADMIN}/audit", params={"action": "admin.setting_changed"}, headers=as_user(ALINA_ADMIN)
    )

    assert response.status_code == 200
    body = response.json()
    # Пропущенные поля получают значения по умолчанию.
    assert body["value"] == {
        "license_warn_days": 60,
        "license_critical_days": 30,
        "inactivity_low_days": 10,
        "inactivity_medium_days": 28,
    }
    assert body["is_default"] is False
    assert audit.json()[0]["after"]["inactivity_low_days"] == 10


async def test_invalid_setting_is_refused(client: AsyncClient) -> None:
    unordered = await client.put(
        f"{ADMIN}/settings/radar_thresholds",
        json={"value": {"inactivity_low_days": 30, "inactivity_medium_days": 20}},
        headers=as_user(ALINA_ADMIN),
    )
    unknown_field = await client.put(
        f"{ADMIN}/settings/radar_thresholds",
        json={"value": {"inactivity_days": 30}},
        headers=as_user(ALINA_ADMIN),
    )
    unknown_key = await client.put(
        f"{ADMIN}/settings/radar_treshold", json={"value": {}}, headers=as_user(ALINA_ADMIN)
    )

    assert unordered.status_code == 422
    assert unordered.json()["code"] == "VALIDATION_ERROR"
    assert unknown_field.json()["errors"][0]["field"] == "value.inactivity_days"
    assert unknown_key.status_code == 404


async def test_radar_follows_the_saved_thresholds(client: AsyncClient) -> None:
    kfu = await find(client, ANNA_KAM, search="КФУ")
    before = await client.get(
        "/api/v1/signals", params={"kind": "inactivity"}, headers=as_user(ALINA_ADMIN)
    )

    await client.put(
        f"{ADMIN}/settings/radar_thresholds",
        json={"value": {"inactivity_low_days": 30, "inactivity_medium_days": 60}},
        headers=as_user(ALINA_ADMIN),
    )
    after = await client.get(
        "/api/v1/signals", params={"kind": "inactivity"}, headers=as_user(ALINA_ADMIN)
    )

    assert [item["interaction"]["id"] for item in before.json()["items"]] == [kfu["id"]]
    # КФУ без изменений 23 дня: при пороге 30 сигнала о простое больше нет.
    assert after.json()["total"] == 0


async def test_team_can_be_created(client: AsyncClient) -> None:
    response = await client.post(
        f"{ADMIN}/teams", json={"name": "Сибирь и Дальний Восток"}, headers=as_user(ALINA_ADMIN)
    )
    teams = await client.get(f"{ADMIN}/teams", headers=as_user(ALINA_ADMIN))

    assert response.status_code == 201
    assert "Сибирь и Дальний Восток" in {team["name"] for team in teams.json()}


async def test_contacts_of_a_foreign_university_are_not_found(
    client: AsyncClient, session: AsyncSession
) -> None:
    # УрФУ ведёт Михаил: Анне этот вуз не виден, значит и его контакты тоже.
    urfu = await university_by(session, "УрФУ")
    created = await client.post(
        f"/api/v1/universities/{urfu.id}/contacts",
        json={"full_name": "Сергей Орлов", "email": "orlov@example.com"},
        headers=as_user(MIKHAIL_KAM),
    )

    card = await client.get(f"/api/v1/universities/{urfu.id}", headers=as_user(ANNA_KAM))
    listed = await client.get(f"/api/v1/universities/{urfu.id}/contacts", headers=as_user(ANNA_KAM))
    added = await client.post(
        f"/api/v1/universities/{urfu.id}/contacts",
        json={"full_name": "Чужой человек"},
        headers=as_user(ANNA_KAM),
    )
    archived = await client.post(
        f"/api/v1/contacts/{created.json()['id']}/archive", headers=as_user(ANNA_KAM)
    )
    missing = await client.get(
        f"/api/v1/universities/{uuid.uuid4()}/contacts", headers=as_user(ALINA_ADMIN)
    )

    assert created.status_code == 201, created.text
    # Карточка вуза и его контакты подчиняются одному правилу видимости.
    assert (card.status_code, listed.status_code) == (404, 404)
    assert added.status_code == 404
    assert archived.status_code == 404
    assert missing.status_code == 404


async def test_archived_contact_leaves_the_list_without_its_data(
    client: AsyncClient, session: AsyncSession
) -> None:
    mgtu = await university_by(session, "МГТУ")
    created = await client.post(
        f"/api/v1/universities/{mgtu.id}/contacts",
        json={"full_name": "Ольга Смирнова", "email": "olga@example.com", "phone": "+7 900"},
        headers=as_user(ANNA_KAM),
    )

    archived = await client.post(
        f"/api/v1/contacts/{created.json()['id']}/archive", headers=as_user(ANNA_KAM)
    )
    listed = await client.get(f"/api/v1/universities/{mgtu.id}/contacts", headers=as_user(ANNA_KAM))
    stored = await session.get(ContactPerson, uuid.UUID(created.json()["id"]))

    assert archived.status_code == 200
    assert (archived.json()["email"], archived.json()["phone"]) == (None, None)
    assert "Ольга Смирнова" not in [item["full_name"] for item in listed.json()]
    assert stored is not None
    assert (stored.email_enc, stored.phone_enc) == (None, None)


async def test_admin_cannot_lock_everyone_out(client: AsyncClient, session: AsyncSession) -> None:
    alina = await user_id(session, ALINA_ADMIN)

    myself = await client.patch(
        f"{ADMIN}/users/{alina}", json={"is_active": False}, headers=as_user(ALINA_ADMIN)
    )
    demoted = await client.patch(
        f"{ADMIN}/users/{alina}", json={"role": "manager"}, headers=as_user(ALINA_ADMIN)
    )
    still_in = await client.get("/api/v1/me", headers=as_user(ALINA_ADMIN))

    # Раньше единственный администратор отключал себя, и вернуть доступ можно было только в базе.
    assert myself.status_code == 422
    assert demoted.status_code == 422
    assert "последний администратор" in demoted.json()["detail"].lower()
    assert still_in.status_code == 200


async def test_role_lives_in_keycloak_when_it_is_the_source(
    client: AsyncClient, session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    mikhail = await user_id(session, "mikhail.volkov@example.com")
    keycloak_mode = get_settings().model_copy(update={"auth_mode": "keycloak"})
    monkeypatch.setattr("app.modules.admin.service.get_settings", lambda: keycloak_mode)

    changed = await client.patch(
        f"{ADMIN}/users/{mikhail}", json={"role": "manager"}, headers=as_user(ALINA_ADMIN)
    )

    # Роль из токена перезаписала бы правку при следующем входе, а аудит соврал бы.
    assert changed.status_code == 422
    assert changed.json()["errors"][0]["field"] == "role"


async def test_first_login_twice_gives_one_employee(session: AsyncSession) -> None:
    claims = {
        "sub": "new-sub-42",
        "email": "novikov@example.com",
        "name": "Новиков Новик Новикович",
        "realm_access": {"roles": ["kam"]},
    }

    first = await _user_from_claims(claims, session)
    second = await _user_from_claims(claims, session)
    count = await session.scalar(
        select(func.count()).select_from(AppUser).where(AppUser.keycloak_sub == "new-sub-42")
    )

    assert first.id == second.id
    assert count == 1
