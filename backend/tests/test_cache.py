"""Кэш действий пользователя: ETag у карточки и файлов, серверный кэш справочников и рейтинга."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import MemoryCache
from app.modules.catalogs.models import Direction, Program, University
from app.modules.metrics.models import ProgramMetric
from tests.api import find, stage_id, upload_pdf
from tests.test_analytics import seed_metrics
from tests.users import ALINA_ADMIN, ANNA_KAM, ROMAN_MANAGER, as_user

CARD = "/api/v1/interactions"
DIRECTIONS = "/api/v1/directions"
RATING = "/api/v1/analytics/rating"


def with_etag(email: str, etag: str) -> dict[str, str]:
    return {**as_user(email), "If-None-Match": etag}


async def test_reopened_card_comes_from_the_browser_cache(client: AsyncClient) -> None:
    mgtu = await find(client, ANNA_KAM, stage_code="signing")
    first = await client.get(f"{CARD}/{mgtu['id']}", headers=as_user(ANNA_KAM))
    etag = first.headers["etag"]

    again = await client.get(f"{CARD}/{mgtu['id']}", headers=with_etag(ANNA_KAM, etag))
    await client.post(
        f"{CARD}/{mgtu['id']}/notes",
        json={"text": "Позвонил проректору, ждём подписи"},
        headers=as_user(ANNA_KAM),
    )
    after_note = await client.get(f"{CARD}/{mgtu['id']}", headers=with_etag(ANNA_KAM, etag))

    assert first.headers["cache-control"] == "private, no-cache"
    assert (again.status_code, again.content) == (304, b"")
    # Заметка меняет карточку, и браузер получает её целиком.
    assert after_note.status_code == 200
    assert after_note.headers["etag"] != etag


async def test_two_kams_do_not_share_a_cached_card(client: AsyncClient) -> None:
    mgtu = await find(client, ANNA_KAM, stage_code="signing")
    mine = await client.get(f"{CARD}/{mgtu['id']}", headers=as_user(ANNA_KAM))

    # Чужая карточка не открывается даже с подходящим ETag: права проверяются до кэша.
    foreign = await client.get(
        f"{CARD}/{mgtu['id']}",
        headers=with_etag("mikhail.volkov@example.com", mine.headers["etag"]),
    )

    assert foreign.status_code == 404
    assert foreign.json()["code"] == "NOT_FOUND"


async def test_catalogue_answers_from_the_cache_until_it_changes(
    client: AsyncClient, session: AsyncSession
) -> None:
    first = await client.get(DIRECTIONS, headers=as_user(ANNA_KAM))
    direction = await session.scalar(select(Direction).order_by(Direction.code).limit(1))
    assert direction is not None
    direction.name = "Переименовано мимо API"
    await session.commit()

    cached = await client.get(DIRECTIONS, headers=as_user(ANNA_KAM))
    created = await client.post(
        "/api/v1/admin/catalogs/directions",
        json={"name": "Квантовые вычисления", "code": "quantum"},
        headers=as_user(ALINA_ADMIN),
    )
    after = await client.get(DIRECTIONS, headers=as_user(ANNA_KAM))

    assert created.status_code == 201, created.text
    # Правка мимо приложения кэшем не видна — зато действие в админке сбрасывает его сразу.
    assert cached.json() == first.json()
    assert [item["name"] for item in after.json()] != [item["name"] for item in first.json()]
    assert "Квантовые вычисления" in {item["name"] for item in after.json()}


async def test_cached_lists_of_different_filters_do_not_mix(client: AsyncClient) -> None:
    everything = await client.get("/api/v1/programs", headers=as_user(ANNA_KAM))
    devops = next(item["direction"]["id"] for item in everything.json())

    filtered = await client.get(
        "/api/v1/programs", params={"direction_id": devops}, headers=as_user(ANNA_KAM)
    )
    repeated = await client.get("/api/v1/programs", headers=as_user(ANNA_KAM))

    assert len(filtered.json()) < len(everything.json())
    assert repeated.json() == everything.json()
    assert repeated.headers["etag"] == everything.headers["etag"]


async def test_rating_is_counted_once_and_recounted_after_a_change(
    client: AsyncClient, session: AsyncSession
) -> None:
    today = datetime.now(UTC).date()
    params: dict[str, Any] = {
        "period_from": str(today - timedelta(days=30)),
        "period_to": str(today),
    }
    first = await client.get(RATING, params=params, headers=as_user(ROMAN_MANAGER))

    university = await session.scalar(select(University).limit(1))
    program = await session.scalar(select(Program).order_by(Program.name).limit(1))
    assert university is not None
    assert program is not None
    session.add(
        ProgramMetric(
            university_id=university.id,
            program_id=program.id,
            period_month=today.replace(day=1),
            metric="applications",
            value=500,
            source="manual",
        )
    )
    await session.commit()
    cached = await client.get(RATING, params=params, headers=as_user(ROMAN_MANAGER))
    await client.put(
        f"/api/v1/programs/{program.id}/priority",
        json={"priority": 7},
        headers=as_user(ROMAN_MANAGER),
    )
    after = await client.get(RATING, params=params, headers=as_user(ROMAN_MANAGER))

    assert cached.json() == first.json()
    assert cached.headers["etag"] == first.headers["etag"]
    # Ручной приоритет виден в рейтинге, а заодно в пересчёт попали новые метрики.
    assert [row["priority"] for row in after.json()["rows"] if row["id"] == str(program.id)] == [7]
    assert after.json() != first.json()


async def test_file_is_downloaded_once(client: AsyncClient) -> None:
    mgtu = await find(client, ANNA_KAM, stage_code="signing")
    uploaded = await upload_pdf(client, ANNA_KAM, mgtu["id"])
    url = f"/api/v1/attachments/{uploaded['id']}/file"

    first = await client.get(url, headers=as_user(ANNA_KAM))
    again = await client.get(url, headers=with_etag(ANNA_KAM, first.headers["etag"]))

    assert first.headers["etag"] == f'"{uploaded["sha256"]}"'
    # Не immutable: после потери доступа браузер обязан спросить сервер и получить 404.
    assert first.headers["cache-control"] == "private, no-cache"
    assert (again.status_code, again.content) == (304, b"")


async def test_ready_report_is_downloaded_once(client: AsyncClient) -> None:
    job = await client.post("/api/v1/reports", json={"format": "json"}, headers=as_user(ANNA_KAM))
    url = f"/api/v1/reports/{job.json()['id']}/file"

    first = await client.get(url, headers=as_user(ANNA_KAM))
    again = await client.get(url, headers=with_etag(ANNA_KAM, first.headers["etag"]))

    assert first.status_code == 200, first.text
    assert first.headers["cache-control"] == "private, no-cache"
    assert (again.status_code, again.content) == (304, b"")


async def test_transition_shows_the_card_anew(client: AsyncClient) -> None:
    kfu = await find(client, ANNA_KAM, search="КФУ")
    first = await client.get(f"{CARD}/{kfu['id']}", headers=as_user(ANNA_KAM))

    await client.post(
        f"{CARD}/{kfu['id']}/transitions",
        json={
            "to_stage_id": await stage_id(client, "documents_exchange"),
            "comment": "Встретились, отправили проект договора",
            "expected_version": kfu["version"],
        },
        headers=as_user(ANNA_KAM),
    )
    after = await client.get(
        f"{CARD}/{kfu['id']}", headers=with_etag(ANNA_KAM, first.headers["etag"])
    )

    assert after.status_code == 200
    assert after.json()["stage"]["code"] == "documents_exchange"


async def test_catalogue_file_with_priorities_refreshes_the_rating(
    client: AsyncClient, session: AsyncSession
) -> None:
    await seed_metrics(session)
    today = datetime.now(UTC).date()
    params: dict[str, Any] = {
        "period_from": str(today - timedelta(days=30)),
        "period_to": str(today),
    }
    first = await client.get(RATING, params=params, headers=as_user(ROMAN_MANAGER))
    program = await session.get(Program, uuid.UUID(first.json()["rows"][0]["id"]))
    assert program is not None
    direction = await session.get(Direction, program.direction_id)
    assert direction is not None

    content = (
        f"Код направления;Название;Приоритет\r\n{direction.code};{program.name};77\r\n".encode(
            "cp1251"
        )
    )
    loaded = await client.post(
        "/api/v1/admin/catalogs/programs/import",
        files={"file": ("программы.csv", content, "text/csv")},
        data={"dry_run": "false"},
        headers=as_user(ALINA_ADMIN),
    )
    after = await client.get(RATING, params=params, headers=as_user(ROMAN_MANAGER))

    assert loaded.json()["updated"] == 1
    # Приоритет из файла виден в рейтинге сразу, а не через пять минут жизни кэша.
    assert [row["priority"] for row in after.json()["rows"] if row["id"] == str(program.id)] == [77]


async def test_memory_cache_forgets_by_itself() -> None:
    cache = MemoryCache()
    await cache.set("cache:catalogs:0:directions", "[]", ttl=60)
    fresh = await cache.get("cache:catalogs:0:directions")

    await cache.set("cache:catalogs:0:products", "[]", ttl=0)
    stale = await cache.get("cache:catalogs:0:products")

    # Запуск без Redis не должен жить с вечным кэшем: обещание «не дольше срока жизни» общее.
    assert fresh == "[]"
    assert stale is None
