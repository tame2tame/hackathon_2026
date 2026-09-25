"""Импорт выгрузки заказчика: подсказка маппинга, предпросмотр, применение и повторный импорт."""

from datetime import date
from typing import Any

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog
from app.modules.catalogs.models import AppUser, University
from app.modules.interactions.models import AssignmentChange, Interaction
from scripts.make_import_fixture import HEADERS, build_workbook
from tests.api import user_id
from tests.users import ALINA_ADMIN, ANNA_KAM, ROMAN_MANAGER, as_user

IMPORTS = "/api/v1/imports"


async def upload(client: AsyncClient, email: str = ROMAN_MANAGER) -> dict[str, Any]:
    response = await client.post(
        IMPORTS,
        files={
            "file": (
                "Выгрузка.xlsx",
                build_workbook(date.today()),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers=as_user(email),
    )
    assert response.status_code == 201, response.text
    batch: dict[str, Any] = response.json()
    return batch


async def preview(
    client: AsyncClient, batch: dict[str, Any], column_map: dict[str, str] | None = None
) -> dict[str, Any]:
    response = await client.put(
        f"{IMPORTS}/{batch['id']}/mapping",
        json={"column_map": column_map or batch["suggested_map"]},
        headers=as_user(ROMAN_MANAGER),
    )
    assert response.status_code == 200, response.text
    previewed: dict[str, Any] = response.json()
    return previewed


async def apply(client: AsyncClient, batch: dict[str, Any]) -> dict[str, Any]:
    response = await client.post(f"{IMPORTS}/{batch['id']}/apply", headers=as_user(ROMAN_MANAGER))
    assert response.status_code == 200, response.text
    result: dict[str, Any] = response.json()
    return result


async def signals_of_kind(client: AsyncClient, kind: str) -> int:
    response = await client.get(
        "/api/v1/signals", params={"kind": kind, "page_size": 1}, headers=as_user(ALINA_ADMIN)
    )
    total: int = response.json()["total"]
    return total


async def test_upload_reads_headers_and_suggests_mapping(client: AsyncClient) -> None:
    batch = await upload(client)

    assert batch["status"] == "uploaded"
    assert batch["headers"] == list(HEADERS)
    assert batch["total_rows"] == 30
    assert batch["suggested_map"]["university"] == "Название ВУЗа"
    assert batch["suggested_map"]["product"] == "ПО"
    assert batch["suggested_map"]["license_valid_until"] == "Срок действия лицензии"
    assert batch["suggested_map"]["manager"] == "ФИО Менеджера"


async def test_kam_cannot_import(client: AsyncClient) -> None:
    response = await client.post(
        IMPORTS,
        files={"file": ("Выгрузка.xlsx", build_workbook(date.today()), "application/vnd.ms-excel")},
        headers=as_user(ANNA_KAM),
    )

    assert response.status_code == 403
    assert response.json()["code"] == "AUTH_FORBIDDEN"


async def test_incomplete_mapping_is_refused(client: AsyncClient) -> None:
    batch = await upload(client)
    without_product = {
        field: header for field, header in batch["suggested_map"].items() if field != "product"
    }

    response = await client.put(
        f"{IMPORTS}/{batch['id']}/mapping",
        json={"column_map": without_product},
        headers=as_user(ROMAN_MANAGER),
    )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "IMPORT_MAPPING_INVALID"
    assert body["errors"] == [{"field": "column_map.product", "message": "Обязательное поле"}]


async def test_preview_sorts_rows_by_resolution(client: AsyncClient) -> None:
    batch = await upload(client)

    previewed = await preview(client, batch)

    assert previewed["status"] == "previewed"
    assert previewed["stats"] == {"total": 30, "new": 25, "conflict": 2, "needs_program": 3}
    conflict = next(row for row in previewed["rows"] if row["resolution"] == "conflict")
    assert "Пётр Сидоров" in (conflict["detail"] or "")


async def test_apply_creates_interactions_and_license_signals(client: AsyncClient) -> None:
    before = await signals_of_kind(client, "license_expiring")
    batch = await upload(client)
    await preview(client, batch)

    result = await apply(client, batch)

    assert (result["created"], result["updated"]) == (25, 0)
    assert (result["conflicts"], result["needs_program"]) == (2, 3)
    # Пять лицензий в фикстуре истекают в ближайший месяц.
    assert await signals_of_kind(client, "license_expiring") == before + 5


async def test_second_import_updates_instead_of_duplicating(client: AsyncClient) -> None:
    first = await upload(client)
    await preview(client, first)
    await apply(client, first)
    total_after_first = (
        await client.get(
            "/api/v1/interactions", params={"page_size": 1}, headers=as_user(ALINA_ADMIN)
        )
    ).json()["total"]

    second = await upload(client)
    previewed = await preview(client, second)
    result = await apply(client, second)

    assert previewed["stats"]["update"] == 25
    assert (result["created"], result["updated"]) == (0, 25)
    total_after_second = (
        await client.get(
            "/api/v1/interactions", params={"page_size": 1}, headers=as_user(ALINA_ADMIN)
        )
    ).json()["total"]
    assert total_after_second == total_after_first


async def test_mapping_can_be_saved_as_profile(client: AsyncClient) -> None:
    batch = await upload(client)

    await client.put(
        f"{IMPORTS}/{batch['id']}/mapping",
        json={"column_map": batch["suggested_map"], "save_as_profile": "Выгрузка заказчика"},
        headers=as_user(ROMAN_MANAGER),
    )
    profiles = await client.get("/api/v1/import-profiles", headers=as_user(ROMAN_MANAGER))

    assert profiles.status_code == 200
    [profile] = profiles.json()
    assert profile["name"] == "Выгрузка заказчика"
    assert profile["column_map"]["university"] == "Название ВУЗа"


async def test_not_a_workbook_is_refused(client: AsyncClient) -> None:
    response = await client.post(
        IMPORTS,
        files={"file": ("Выгрузка.xlsx", b"not a workbook at all", "application/vnd.ms-excel")},
        headers=as_user(ROMAN_MANAGER),
    )

    assert response.status_code == 415
    assert response.json()["code"] == "FILE_TYPE_NOT_ALLOWED"


async def upload_csv(client: AsyncClient, rows: list[str], email: str) -> dict[str, Any]:
    content = ("\r\n".join(["Название ВУЗа;Вендор;ПО;ФИО Менеджера", *rows]) + "\r\n").encode()
    response = await client.post(
        IMPORTS, files={"file": ("выгрузка.csv", content, "text/csv")}, headers=as_user(email)
    )
    assert response.status_code == 201, response.text
    batch: dict[str, Any] = response.json()
    return batch


async def mgtu_record(session: AsyncSession) -> Interaction:
    record = await session.scalar(
        select(Interaction)
        .join(University, University.id == Interaction.university_id)
        .where(University.short_name == "МГТУ")
    )
    assert record is not None
    return record


async def test_import_does_not_take_a_record_of_another_team(
    client: AsyncClient, session: AsyncSession
) -> None:
    # Запись МГТУ передаём КАМу другой команды: руководителю Роману она больше не видна.
    stranger = AppUser(email="stranger@example.com", full_name="Чужой КАМ", role="kam")
    session.add(stranger)
    await session.flush()
    record = await mgtu_record(session)
    record.owner_user_id = stranger.id
    await session.commit()

    batch = await upload_csv(client, ["МГТУ им. Н. Э. Баумана;Базис;Базис;"], ROMAN_MANAGER)
    previewed = await preview(client, batch)
    result = await apply(client, batch)
    await session.refresh(record)
    changes = await session.scalar(
        select(func.count())
        .select_from(AssignmentChange)
        .where(AssignmentChange.interaction_id == record.id)
    )

    assert previewed["stats"].get("update", 0) == 0
    assert previewed["stats"]["conflict"] == 1
    assert (result["updated"], result["conflicts"]) == (0, 1)
    # Раньше пустая колонка менеджера делала владельцем того, кто загружает файл.
    assert record.owner_user_id == stranger.id
    assert changes == 0


async def test_empty_manager_column_keeps_the_owner(
    client: AsyncClient, session: AsyncSession
) -> None:
    record = await mgtu_record(session)
    owner_before = record.owner_user_id

    batch = await upload_csv(client, ["МГТУ им. Н. Э. Баумана;Базис;Базис;"], ROMAN_MANAGER)
    await preview(client, batch)
    result = await apply(client, batch)
    await session.refresh(record)

    assert result["updated"] == 1
    assert record.owner_user_id == owner_before


async def test_manager_in_the_file_reassigns_with_history(
    client: AsyncClient, session: AsyncSession
) -> None:
    record = await mgtu_record(session)
    mikhail = await user_id(session, "mikhail.volkov@example.com")

    batch = await upload_csv(
        client, ["МГТУ им. Н. Э. Баумана;Базис;Базис;Михаил Волков"], ROMAN_MANAGER
    )
    await preview(client, batch)
    await apply(client, batch)
    await session.refresh(record)
    change = await session.scalar(
        select(AssignmentChange).where(AssignmentChange.interaction_id == record.id)
    )
    audit = await session.scalar(
        select(AuditLog).where(
            AuditLog.action == "interaction.owner_change", AuditLog.entity_id == record.id
        )
    )

    # Смена ответственного из файла идёт тем же путём, что в карточке: история и аудит.
    assert record.owner_user_id == mikhail
    assert change is not None
    assert change.to_user_id == mikhail
    assert audit is not None
