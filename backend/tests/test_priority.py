"""Ручной приоритет курсов: рейтинг считает данные, порядок продвижения задаёт руководитель."""

from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog
from app.modules.catalogs.models import Program
from tests.test_analytics import RATING, seed_metrics
from tests.test_catalog_files import load
from tests.users import ALINA_ADMIN, ANNA_KAM, ROMAN_MANAGER, as_user

PROGRAMS = "/api/v1/programs"


async def test_marked_course_goes_first_in_the_catalogue(client: AsyncClient) -> None:
    programs = (await client.get(PROGRAMS, headers=as_user(ANNA_KAM))).json()
    last = programs[-1]

    changed = await client.put(
        f"{PROGRAMS}/{last['id']}/priority", json={"priority": 90}, headers=as_user(ROMAN_MANAGER)
    )
    after = (await client.get(PROGRAMS, headers=as_user(ANNA_KAM))).json()

    assert changed.status_code == 200, changed.text
    assert changed.json()["priority"] == 90
    # Демо-данные уже размечены руководителем, поэтому проверяем именно перестановку.
    assert programs[0]["name"] == "Анализ данных"
    assert after[0]["id"] == last["id"]
    assert [item["priority"] for item in after] == sorted(
        (item["priority"] for item in after), reverse=True
    )


async def test_priority_changes_the_order_but_not_the_place(
    client: AsyncClient, session: AsyncSession
) -> None:
    await seed_metrics(session)
    today = datetime.now(UTC).date()
    params = {"period_from": str(today - timedelta(days=30)), "period_to": str(today)}
    by_score = (await client.get(RATING, params=params, headers=as_user(ROMAN_MANAGER))).json()
    outsider = by_score["rows"][-1]

    await client.put(
        f"{PROGRAMS}/{outsider['id']}/priority",
        json={"priority": 100},
        headers=as_user(ROMAN_MANAGER),
    )
    by_priority = (
        await client.get(
            RATING, params={**params, "order": "priority"}, headers=as_user(ROMAN_MANAGER)
        )
    ).json()

    assert by_score["order"] == "score"
    assert outsider["place"] > 1
    first = by_priority["rows"][0]
    # Наверху списка — отмеченный руководителем курс, но место у него осталось прежним.
    assert (first["id"], first["priority"]) == (outsider["id"], 100)
    assert first["place"] == outsider["place"]
    assert {row["place"] for row in by_priority["rows"]} == {
        row["place"] for row in by_score["rows"]
    }


async def test_priority_is_written_to_the_audit(client: AsyncClient, session: AsyncSession) -> None:
    program = await session.scalar(select(Program).order_by(Program.name).limit(1))
    assert program is not None

    await client.put(
        f"{PROGRAMS}/{program.id}/priority", json={"priority": 5}, headers=as_user(ALINA_ADMIN)
    )

    entry = await session.scalar(
        select(AuditLog).where(AuditLog.action == "catalog.program_priority_changed")
    )
    assert entry is not None
    assert (entry.entity_id, entry.after) == (program.id, {"priority": 5})


async def test_kam_does_not_reorder_the_catalogue(
    client: AsyncClient, session: AsyncSession
) -> None:
    program = await session.scalar(select(Program).limit(1))
    assert program is not None

    by_kam = await client.put(
        f"{PROGRAMS}/{program.id}/priority", json={"priority": 10}, headers=as_user(ANNA_KAM)
    )
    too_big = await client.put(
        f"{PROGRAMS}/{program.id}/priority", json={"priority": 101}, headers=as_user(ROMAN_MANAGER)
    )

    assert by_kam.status_code == 403
    assert too_big.status_code == 422
    assert too_big.json()["code"] == "VALIDATION_ERROR"


async def test_priority_travels_with_the_catalogue_file(client: AsyncClient) -> None:
    content = "Код направления;Название;Приоритет\r\ndevops;DevOps-инженерия;55\r\n".encode(
        "cp1251"
    )

    loaded = await load(client, "programs", "программы.csv", content, dry_run=False)
    broken = await load(
        client,
        "programs",
        "программы.csv",
        "Код направления;Название;Приоритет\r\ndevops;DevOps-инженерия;много\r\n".encode("cp1251"),
        dry_run=False,
    )
    exported = await client.get(
        "/api/v1/admin/catalogs/programs/export",
        params={"format": "json"},
        headers=as_user(ALINA_ADMIN),
    )

    assert loaded["rows"][0]["action"] == "updated"
    assert broken["rows"][0]["detail"] == "Приоритет — число от 0 до 100, а не «много»"
    row = next(item for item in exported.json()["items"] if item["name"] == "DevOps-инженерия")
    assert row["priority"] == "55"
