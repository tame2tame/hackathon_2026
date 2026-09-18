"""Списки обучающихся и преподавателей: ведение, файл, персональные данные и аудит."""

from typing import Any

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog
from app.modules.participants.models import Participant
from tests.api import find
from tests.users import ALINA_ADMIN, ANNA_KAM, MIKHAIL_KAM, ROMAN_MANAGER, as_user

CSV_LIST = (
    "ФИО;Email;Роль\r\n"
    "Ковалёв Артём Игоревич;a.kovalev@student.example.com;обучающийся\r\n"
    "Новиков Пётр Ильич;p.novikov@student.example.com;обучающийся\r\n"
    "Громова Ольга Петровна;o.gromova@itmo.example.com;преподаватель\r\n"
)


async def classes(client: AsyncClient) -> dict[str, Any]:
    """Запись, по которой идут занятия: у неё в демо-данных есть группа."""
    return await find(client, ANNA_KAM, stage_code="classes")


async def load(
    client: AsyncClient, interaction_id: str, content: bytes, *, dry_run: bool, **form: str
) -> dict[str, Any]:
    response = await client.post(
        f"/api/v1/interactions/{interaction_id}/participants/import",
        files={"file": ("группа.csv", content, "text/csv")},
        data={"dry_run": str(dry_run).lower(), **form},
        headers=as_user(ANNA_KAM),
    )
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


async def test_demo_group_is_visible_with_hidden_addresses(client: AsyncClient) -> None:
    itmo = await classes(client)

    response = await client.get(
        f"/api/v1/interactions/{itmo['id']}/participants", headers=as_user(ANNA_KAM)
    )
    teachers = await client.get(
        f"/api/v1/interactions/{itmo['id']}/participants",
        params={"role": "teacher"},
        headers=as_user(ANNA_KAM),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["counts"] == {"students": 3, "teachers": 1}
    student = next(item for item in body["items"] if item["role"] == "student")
    # В списке видно, чья это почта, но не сам адрес.
    assert student["email"].startswith("a***@") or student["email"].count("*") == 3
    assert "@" in student["email"]
    assert student["has_email"] is True
    assert [item["full_name"] for item in teachers.json()["items"]] == ["Громова Ольга Петровна"]


async def test_address_is_shown_by_request_and_written_to_the_audit(
    client: AsyncClient, session: AsyncSession
) -> None:
    itmo = await classes(client)
    listed = await client.get(
        f"/api/v1/interactions/{itmo['id']}/participants", headers=as_user(ANNA_KAM)
    )
    teacher = next(item for item in listed.json()["items"] if item["role"] == "teacher")

    contact = await client.get(
        f"/api/v1/participants/{teacher['id']}/contact", headers=as_user(ANNA_KAM)
    )
    foreign = await client.get(
        f"/api/v1/participants/{teacher['id']}/contact", headers=as_user(MIKHAIL_KAM)
    )

    assert contact.json()["email"] == "o.gromova@itmo.example.com"
    assert foreign.status_code == 404
    entry = await session.scalar(
        select(AuditLog).where(AuditLog.action == "participant.contact_viewed")
    )
    assert entry is not None
    assert entry.after == {"role": "teacher"}


async def test_list_of_a_foreign_record_is_not_found(client: AsyncClient) -> None:
    itmo = await classes(client)

    listed = await client.get(
        f"/api/v1/interactions/{itmo['id']}/participants", headers=as_user(MIKHAIL_KAM)
    )
    added = await client.post(
        f"/api/v1/interactions/{itmo['id']}/participants",
        json={"full_name": "Кто-то чужой", "role": "student"},
        headers=as_user(MIKHAIL_KAM),
    )

    assert listed.status_code == 404
    assert added.status_code == 404
    assert added.json()["code"] == "NOT_FOUND"


async def test_person_is_added_once(client: AsyncClient) -> None:
    itmo = await classes(client)
    payload = {"full_name": "Белов Иван Иванович", "email": "i.belov@student.example.com"}

    added = await client.post(
        f"/api/v1/interactions/{itmo['id']}/participants", json=payload, headers=as_user(ANNA_KAM)
    )
    again = await client.post(
        f"/api/v1/interactions/{itmo['id']}/participants", json=payload, headers=as_user(ANNA_KAM)
    )
    broken = await client.post(
        f"/api/v1/interactions/{itmo['id']}/participants",
        json={"full_name": "Белов Иван Иванович", "email": "не почта"},
        headers=as_user(ANNA_KAM),
    )

    assert added.status_code == 201, added.text
    assert (added.json()["role"], added.json()["source"]) == ("student", "manual")
    assert again.status_code == 422
    assert again.json()["code"] == "VALIDATION_ERROR"
    assert broken.status_code == 422


async def test_leaving_student_takes_their_address_with_them(
    client: AsyncClient, session: AsyncSession
) -> None:
    itmo = await classes(client)
    listed = await client.get(
        f"/api/v1/interactions/{itmo['id']}/participants", headers=as_user(ANNA_KAM)
    )
    student = next(item for item in listed.json()["items"] if item["role"] == "student")

    removed = await client.delete(
        f"/api/v1/participants/{student['id']}", headers=as_user(ROMAN_MANAGER)
    )
    after = await client.get(
        f"/api/v1/interactions/{itmo['id']}/participants", headers=as_user(ANNA_KAM)
    )
    gone = await client.get(
        f"/api/v1/participants/{student['id']}/contact", headers=as_user(ANNA_KAM)
    )

    assert removed.status_code == 204
    assert after.json()["counts"]["students"] == 2
    assert gone.status_code == 404
    row = await session.get(Participant, student["id"])
    assert row is not None
    # Строка осталась для истории, но персональных данных в ней больше нет.
    assert (row.email_enc, row.email_fp) == (None, None)


async def test_the_same_file_loaded_twice_does_not_double_the_group(client: AsyncClient) -> None:
    itmo = await classes(client)
    content = CSV_LIST.encode("cp1251")

    preview = await load(client, itmo["id"], content, dry_run=True)
    applied = await load(client, itmo["id"], content, dry_run=False)
    again = await load(client, itmo["id"], content, dry_run=False)
    listed = await client.get(
        f"/api/v1/interactions/{itmo['id']}/participants", headers=as_user(ANNA_KAM)
    )

    assert (preview["dry_run"], preview["created"]) == (True, 1)
    # Двое из файла уже есть в демо-группе: они находятся по почте и не задваиваются.
    assert (applied["created"], applied["unchanged"]) == (1, 2)
    assert (again["created"], again["unchanged"]) == (0, 3)
    assert listed.json()["counts"] == {"students": 4, "teachers": 1}


async def test_broken_rows_are_reported_one_by_one(client: AsyncClient) -> None:
    itmo = await classes(client)
    content = (
        "ФИО;Email;Роль\r\n"
        ";nobody@example.com;обучающийся\r\n"
        "Петров Пётр;не почта;обучающийся\r\n"
        "Сидоров Сидор;s.sidorov@example.com;кто-то ещё\r\n"
        "Иванов Иван;i.ivanov@example.com;\r\n"
    ).encode()

    result = await load(client, itmo["id"], content, dry_run=False, role="teacher")
    no_column = await client.post(
        f"/api/v1/interactions/{itmo['id']}/participants/import",
        files={
            "file": (
                "группа.csv",
                "Почта;Роль\r\nx@example.com;обучающийся\r\n".encode(),
                "text/csv",
            )
        },
        headers=as_user(ANNA_KAM),
    )

    actions = [(row["row_no"], row["action"]) for row in result["rows"]]
    assert actions == [(1, "error"), (2, "error"), (3, "error"), (4, "created")]
    assert result["rows"][1]["detail"] == "Это не почта: «не почта»"
    assert result["rows"][2]["detail"] == "Не понятно, обучающийся или преподаватель: «кто-то ещё»"
    # Роль из формы достаётся строкам без колонки «Роль».
    assert no_column.status_code == 422
    assert no_column.json()["code"] == "IMPORT_MAPPING_INVALID"


async def test_export_loads_back_unchanged_and_is_audited(
    client: AsyncClient, session: AsyncSession
) -> None:
    itmo = await classes(client)

    exported = await client.get(
        f"/api/v1/interactions/{itmo['id']}/participants/export",
        params={"format": "csv", "encoding": "windows-1251"},
        headers=as_user(ANNA_KAM),
    )
    back = await load(client, itmo["id"], exported.content, dry_run=True)
    by_admin = await client.get(
        f"/api/v1/interactions/{itmo['id']}/participants/export",
        params={"format": "json"},
        headers=as_user(ALINA_ADMIN),
    )

    assert exported.status_code == 200, exported.text
    assert "ФИО" in exported.content.decode("cp1251")
    assert (back["created"], back["unchanged"], back["errors"]) == (0, 4, 0)
    assert len(by_admin.json()["items"]) == 4
    entries = list(
        await session.scalars(select(AuditLog).where(AuditLog.action == "participant.exported"))
    )
    assert [entry.after["format"] for entry in entries] == ["csv", "json"]
