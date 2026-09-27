"""Отчёты: форматы файлов, состояние задания, этап на конец периода и предел размера."""

import json
import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

import arq
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import worker
from app.core.config import Settings
from app.core.security import current_user_for
from app.modules.catalogs.models import AppUser, University
from app.modules.reports import query
from app.modules.reports import service as reports_service
from app.modules.reports.models import ReportJob
from app.modules.reports.schemas import ReportCreate
from app.modules.reports.service import create_job
from tests.users import ALINA_ADMIN, ANNA_KAM, MIKHAIL_KAM, as_user

REPORTS = "/api/v1/reports"
OLE2 = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


async def order(client: AsyncClient, email: str = ANNA_KAM, **params: Any) -> dict[str, Any]:
    response = await client.post(REPORTS, json=params, headers=as_user(email))
    assert response.status_code == 202, response.text
    job: dict[str, Any] = response.json()
    return job


async def download(client: AsyncClient, job_id: str, email: str = ANNA_KAM) -> bytes:
    response = await client.get(f"{REPORTS}/{job_id}/file", headers=as_user(email))
    assert response.status_code == 200, response.text
    return response.content


async def test_report_row_count_matches_the_list(client: AsyncClient) -> None:
    listed = await client.get(
        "/api/v1/interactions", params={"page_size": 1}, headers=as_user(ANNA_KAM)
    )

    job = await order(client, format="json")

    assert job["status"] == "done"
    assert job["progress"] == 100
    assert job["row_count"] == listed.json()["total"]


@pytest.mark.parametrize(
    ("fmt", "signature"),
    [("xlsx", b"PK"), ("xls", OLE2), ("pdf", b"%PDF"), ("json", b"[")],
)
async def test_every_format_produces_its_own_file(
    client: AsyncClient, fmt: str, signature: bytes
) -> None:
    job = await order(client, format=fmt)

    content = await download(client, job["id"])

    assert content.startswith(signature)


async def test_json_report_holds_the_chosen_columns(client: AsyncClient) -> None:
    job = await order(client, format="json", columns=["university", "stage", "signals"])

    rows = json.loads(await download(client, job["id"]))

    assert len(rows) == 4
    assert set(rows[0]) == {"Вуз", "Этап на конец периода", "Сигналы"}


async def test_report_for_a_past_period_shows_that_period_stage(client: AsyncClient) -> None:
    today = date.today()

    now_report = await order(client, format="json", search="МГТУ")
    past_report = await order(
        client, format="json", search="МГТУ", period_to=str(today - timedelta(days=45))
    )

    now_rows = json.loads(await download(client, now_report["id"]))
    past_rows = json.loads(await download(client, past_report["id"]))
    assert now_rows[0]["Этап на конец периода"] == "Подписание"
    # Сорок пять дней назад взаимодействие ещё не дошло до подписания.
    assert past_rows[0]["Этап на конец периода"] == "Обмен документами"


async def test_unknown_column_is_refused(client: AsyncClient) -> None:
    response = await client.post(
        REPORTS, json={"format": "json", "columns": ["вуз"]}, headers=as_user(ANNA_KAM)
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


async def test_report_over_the_limit_is_refused(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(query, "MAX_ROWS", 1)

    response = await client.post(REPORTS, json={"format": "json"}, headers=as_user(ANNA_KAM))

    assert response.status_code == 422
    assert response.json()["code"] == "REPORT_TOO_LARGE"


async def test_foreign_report_is_not_found(client: AsyncClient) -> None:
    job = await order(client, format="json")

    state = await client.get(f"{REPORTS}/{job['id']}", headers=as_user(MIKHAIL_KAM))
    file = await client.get(f"{REPORTS}/{job['id']}/file", headers=as_user(MIKHAIL_KAM))

    assert (state.status_code, file.status_code) == (404, 404)


async def test_admin_can_look_at_any_report(client: AsyncClient) -> None:
    job = await order(client, format="json")

    state = await client.get(f"{REPORTS}/{job['id']}", headers=as_user(ALINA_ADMIN))

    assert state.status_code == 200


async def test_file_of_an_unfinished_report_is_not_found(
    client: AsyncClient, session: AsyncSession
) -> None:
    job = ReportJob(
        requested_by=(await session.scalar(_own_user_id())),
        params={"format": "json", "columns": ["university"]},
        format="json",
        status="queued",
        progress=0,
    )
    session.add(job)
    await session.commit()

    response = await client.get(f"{REPORTS}/{job.id}/file", headers=as_user(ANNA_KAM))

    assert response.status_code == 404


async def test_ten_reports_in_a_row_all_finish(client: AsyncClient) -> None:
    jobs = [await order(client, format="json") for _ in range(10)]

    listed = await client.get(REPORTS, headers=as_user(ANNA_KAM))

    assert {job["status"] for job in jobs} == {"done"}
    assert len(listed.json()) >= 10
    assert all(job["finished_at"] is not None for job in jobs)


def _own_user_id() -> Any:
    from sqlalchemy import select

    from app.modules.catalogs.models import AppUser

    return select(AppUser.id).where(AppUser.email == ANNA_KAM)


async def test_report_params_keep_the_period(client: AsyncClient, session: AsyncSession) -> None:
    yesterday = datetime.now(UTC).date() - timedelta(days=1)

    job = await order(client, format="json", period_from=str(yesterday - timedelta(days=30)))

    stored = await session.get(ReportJob, uuid.UUID(job["id"]))
    assert stored is not None
    assert stored.params["period_from"] == str(yesterday - timedelta(days=30))


class _SessionFactory:
    """Сессия теста вместо своей: воркер ходит в ту же транзакцию, что и проверка."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def __call__(self) -> "_SessionFactory":
        return self

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, *exc: object) -> None:
        return None


async def test_report_from_the_worker_keeps_the_access_rules(
    client: AsyncClient, session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    anna = await session.scalar(select(AppUser).where(AppUser.email == ANNA_KAM))
    mgtu = await session.scalar(select(University).where(University.short_name == "МГТУ"))
    assert anna is not None
    assert mgtu is not None
    job = await create_job(
        session,
        await current_user_for(session, anna),
        ReportCreate(format="json", columns=["university"]),
    )
    rule = await client.post(
        "/api/v1/admin/access-rules",
        json={
            "subject_user_id": str(anna.id),
            "effect": "deny",
            "scope_kind": "university",
            "scope_id": str(mgtu.id),
        },
        headers=as_user(ALINA_ADMIN),
    )
    assert rule.status_code == 201, rule.text
    monkeypatch.setattr(worker, "get_sessionmaker", lambda: _SessionFactory(session))

    status = await worker.build_report({}, str(job.id), str(anna.id))

    assert status == "done"
    rows = json.loads(await download(client, str(job.id)))
    # Отчёт из очереди подчиняется тем же правилам доступа, что и список в интерфейсе.
    assert rows
    assert {"Вуз": "МГТУ им. Н. Э. Баумана"} not in rows


async def test_unfinished_report_is_not_a_cached_file(client: AsyncClient) -> None:
    job = await order(client, format="json")
    ready = await client.get(f"{REPORTS}/{job['id']}/file", headers=as_user(ANNA_KAM))
    etag = ready.headers["etag"]

    pending = await client.post(REPORTS, json={"format": "pdf"}, headers=as_user(ANNA_KAM))
    unfinished = await client.get(
        f"{REPORTS}/{pending.json()['id']}/file",
        headers={**as_user(ANNA_KAM), "If-None-Match": etag},
    )

    assert ready.status_code == 200
    # Неготовый отчёт не должен притворяться неизменившимся файлом.
    assert unfinished.status_code in (200, 404)
    if unfinished.status_code == 404:
        assert unfinished.json()["code"] == "NOT_FOUND"


async def test_queue_connection_is_closed_after_the_order(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    closed: list[bool] = []

    class Pool:
        async def enqueue_job(self, *args: Any) -> None:
            return None

        async def aclose(self) -> None:
            closed.append(True)

    async def create_pool(*args: Any, **kwargs: Any) -> Pool:
        return Pool()

    # Очередь как на стенде: Redis задан, задание уходит воркеру.
    monkeypatch.setattr(
        reports_service,
        "get_settings",
        lambda: Settings(app_env="local", auth_mode="dev", redis_url="redis://queue:6379/0"),
    )
    monkeypatch.setattr(arq, "create_pool", create_pool)

    response = await client.post(
        "/api/v1/reports", json={"format": "json"}, headers=as_user(ANNA_KAM)
    )

    assert response.status_code == 202, response.text
    # Раньше каждый заказ оставлял открытое соединение с Redis до конца процесса.
    assert closed == [True]
