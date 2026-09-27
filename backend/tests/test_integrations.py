"""Интеграции: метрики LMS, заявки сайта, правила сопоставления и изоляция отказов."""

from collections import Counter
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalogs.models import AppUser, Program, ProgramProduct, Team, University
from app.modules.integrations.clients import (
    ApplicationRecord,
    CourseMetrics,
    HttpSiteClient,
    MoodleLmsClient,
    SourceUnavailableError,
    source_token,
)
from app.modules.integrations.models import IntegrationSource, SiteApplication
from app.modules.integrations.service import (
    LMS_NAME,
    SITE_NAME,
    ensure_sources,
    sync_all,
    sync_source,
)
from app.modules.interactions.models import Interaction
from app.modules.metrics.models import ProgramMetric
from tests.api import find
from tests.users import ALINA_ADMIN, ANNA_KAM, ROMAN_MANAGER, as_user

MONTH = datetime.now(UTC).date().replace(day=1)


class FakeLms:
    def __init__(self, metrics: list[CourseMetrics]) -> None:
        self._metrics = metrics

    async def fetch_metrics(self) -> list[CourseMetrics]:
        return self._metrics


class FakeSite:
    def __init__(self, records: list[ApplicationRecord]) -> None:
        self._records = records

    async def fetch_applications(self) -> list[ApplicationRecord]:
        return self._records


class BrokenSource:
    async def fetch_metrics(self) -> list[CourseMetrics]:
        raise SourceUnavailableError("соединение разорвано")

    async def fetch_applications(self) -> list[ApplicationRecord]:
        raise SourceUnavailableError("соединение разорвано")


def lms_metrics() -> list[CourseMetrics]:
    return [
        CourseMetrics("МГТУ", "DevOps-инженерия", MONTH, students=40, streams=2),
        CourseMetrics("Неизвестный вуз", "DevOps-инженерия", MONTH, students=10, streams=1),
    ]


def site_records() -> list[ApplicationRecord]:
    now = datetime.now(UTC)
    return [
        ApplicationRecord("site-1", "ИТМО", "Анализ данных", "Приёмная", None, now),
        ApplicationRecord("site-2", "Неизвестный вуз", "Робототехника", None, None, now),
    ]


async def source_of(session: AsyncSession, name: str) -> IntegrationSource:
    await ensure_sources(session)
    source = await session.scalar(select(IntegrationSource).where(IntegrationSource.name == name))
    assert source is not None
    return source


async def test_sources_are_created_once(session: AsyncSession) -> None:
    first = await ensure_sources(session)
    second = await ensure_sources(session)

    assert {source.name for source in first} == {LMS_NAME, SITE_NAME}
    assert len(second) == 2
    assert await session.scalar(select(func.count()).select_from(IntegrationSource)) == 2


async def test_lms_metrics_are_stored_and_not_duplicated(session: AsyncSession) -> None:
    source = await source_of(session, LMS_NAME)

    first = await sync_source(session, source, FakeLms(lms_metrics()))
    second = await sync_source(session, source, FakeLms(lms_metrics()))

    assert (first.status, second.status) == ("done", "done")
    # Вуза «Неизвестный вуз» нет в справочнике — такая строка пропускается.
    assert first.stats["skipped"] == 1
    assert second.stats["updated"] == 2
    stored = await session.scalars(select(ProgramMetric).where(ProgramMetric.source == "lms"))
    values = {metric.metric: metric.value for metric in stored}
    assert values == {"students": 40, "streams": 2}


async def test_site_application_matches_existing_interaction(session: AsyncSession) -> None:
    source = await source_of(session, SITE_NAME)

    run = await sync_source(session, source, FakeSite(site_records()))

    assert run.status == "done"
    assert (run.stats["matched"], run.stats["unmatched"]) == (1, 1)
    matched = await session.scalar(
        select(SiteApplication).where(SiteApplication.external_id == "site-1")
    )
    assert matched is not None
    assert matched.interaction_id is not None
    unmatched = await session.scalar(
        select(SiteApplication).where(SiteApplication.external_id == "site-2")
    )
    assert unmatched is not None
    assert (unmatched.match_status, unmatched.interaction_id) == ("unmatched", None)


async def test_unknown_program_creates_an_interaction(session: AsyncSession) -> None:
    source = await source_of(session, SITE_NAME)
    before = await session.scalar(select(func.count()).select_from(Interaction))
    # Вуз и программа есть в справочниках, но такой связки ещё нет.
    record = ApplicationRecord(
        "site-new", "НГУ", "Веб-разработка", "Декан", "Просят курс", datetime.now(UTC)
    )

    run = await sync_source(session, source, FakeSite([record]))

    after = await session.scalar(select(func.count()).select_from(Interaction))
    assert run.stats["interactions_created"] == 1
    assert (after or 0) == (before or 0) + 1
    created = await session.scalar(
        select(Interaction).where(Interaction.source == "site").order_by(Interaction.created_at)
    )
    assert created is not None
    assert created.owner_user_id is not None


async def test_only_product_of_a_program_is_its_default(session: AsyncSession) -> None:
    source = await source_of(session, SITE_NAME)
    program = await session.scalar(select(Program).where(Program.name == "Веб-разработка"))
    assert program is not None
    # Флаг не проставлен, но продукт у программы один: выбирать нечего.
    await session.execute(
        update(ProgramProduct)
        .where(ProgramProduct.program_id == program.id)
        .values(is_default=False)
    )
    linked = await session.scalar(
        select(ProgramProduct.product_id).where(ProgramProduct.program_id == program.id)
    )
    record = ApplicationRecord(
        "site-only", "НГУ", "Веб-разработка", "Декан", "Просят курс", datetime.now(UTC)
    )

    run = await sync_source(session, source, FakeSite([record]))

    application = await session.scalar(
        select(SiteApplication).where(SiteApplication.external_id == "site-only")
    )
    assert run.stats["interactions_created"] == 1
    assert application is not None
    assert application.match_status == "matched"
    created = await session.get(Interaction, application.interaction_id)
    assert created is not None
    assert created.product_id == linked


async def test_repeated_sync_keeps_one_application(session: AsyncSession) -> None:
    source = await source_of(session, SITE_NAME)

    await sync_source(session, source, FakeSite(site_records()))
    await sync_source(session, source, FakeSite(site_records()))

    total = await session.scalar(select(func.count()).select_from(SiteApplication))
    assert total == 2


async def test_broken_source_is_logged_and_others_keep_working(session: AsyncSession) -> None:
    lms = await source_of(session, LMS_NAME)
    site = await source_of(session, SITE_NAME)

    failed = await sync_source(session, lms, BrokenSource())
    healthy = await sync_source(session, site, FakeSite(site_records()))

    assert (failed.status, failed.error_code) == ("failed", "INTEGRATION_UNAVAILABLE")
    assert failed.finished_at is not None
    assert healthy.status == "done"
    assert lms.last_sync_at is None
    assert site.last_sync_at is not None


async def test_sync_all_visits_every_source(session: AsyncSession) -> None:
    """Обход идёт по всем источникам. Адреса в тестах мёртвые, поэтому оба ответа — отказ."""
    sources = await ensure_sources(session)

    runs = await sync_all(session, datetime.now(UTC))

    assert len(runs) == len(sources)
    assert {run.source_id for run in runs} == {source.id for source in sources}
    assert all(run.finished_at is not None for run in runs)
    assert Counter(run.error_code for run in runs)["INTEGRATION_UNAVAILABLE"] == 2


async def test_moodle_client_reads_the_mock(session: AsyncSession) -> None:
    from mocks.lms import app as lms_app

    client = MoodleLmsClient("http://lms.test", transport=httpx.ASGITransport(app=lms_app))

    metrics = await client.fetch_metrics()

    assert metrics
    assert metrics[0].students > 0
    assert metrics[0].period_month.day == 1


async def test_site_client_reads_the_mock() -> None:
    from mocks.site import app as site_app

    client = HttpSiteClient("http://site.test", transport=httpx.ASGITransport(app=site_app))

    records = await client.fetch_applications()

    assert records
    assert all(record.external_id.startswith("site-") for record in records)
    # Часть заявок мок отдаёт с вузами вне справочника — они и попадут в очередь на разбор.
    assert any(record.university_name == "Университет без справочника" for record in records)


async def test_manager_sees_sources_and_kam_does_not(client: AsyncClient) -> None:
    manager = await client.get("/api/v1/integrations", headers=as_user(ROMAN_MANAGER))
    kam = await client.get("/api/v1/integrations", headers=as_user(ANNA_KAM))

    assert manager.status_code == 200
    assert kam.status_code == 403


async def test_manual_match_binds_application_to_interaction(
    client: AsyncClient, session: AsyncSession
) -> None:
    source = await source_of(session, SITE_NAME)
    await sync_source(session, source, FakeSite(site_records()))
    await session.commit()
    interaction = await find(client, ANNA_KAM, stage_code="signing")
    application = await session.scalar(
        select(SiteApplication).where(SiteApplication.external_id == "site-2")
    )
    assert application is not None

    response = await client.post(
        f"/api/v1/site-applications/{application.id}/match",
        json={"interaction_id": interaction["id"]},
        headers=as_user(ROMAN_MANAGER),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["match_status"] == "matched"
    assert body["interaction_id"] == interaction["id"]


async def test_unmatched_queue_is_filtered(client: AsyncClient, session: AsyncSession) -> None:
    source = await source_of(session, SITE_NAME)
    await sync_source(session, source, FakeSite(site_records()))
    await session.commit()

    response = await client.get(
        "/api/v1/site-applications",
        params={"match_status": "unmatched"},
        headers=as_user(ROMAN_MANAGER),
    )

    assert response.status_code == 200
    assert {item["external_id"] for item in response.json()} == {"site-2"}


async def test_applications_metric_counts_by_month(session: AsyncSession) -> None:
    source = await source_of(session, SITE_NAME)
    now = datetime.now(UTC)
    records = [
        ApplicationRecord(
            f"site-m{index}", "ИТМО", "Анализ данных", None, None, now - timedelta(hours=index)
        )
        for index in range(3)
    ]

    await sync_source(session, source, FakeSite(records))

    metric = await session.scalar(
        select(ProgramMetric).where(
            ProgramMetric.source == "site", ProgramMetric.metric == "applications"
        )
    )
    assert metric is not None
    assert metric.value == 3


async def test_disabled_source_is_skipped_by_the_schedule(
    client: AsyncClient, session: AsyncSession
) -> None:
    sources = {source.kind: source for source in await ensure_sources(session)}
    turned_off = await client.patch(
        f"/api/v1/integrations/{sources['lms'].id}",
        json={"pull_enabled": False},
        headers=as_user(ALINA_ADMIN),
    )

    # Выключили через API, то есть другой сессией: воркер, как и здесь, читает свежее состояние.
    session.expire_all()
    runs = await sync_all(session, datetime.now(UTC))

    assert turned_off.status_code == 200, turned_off.text
    assert turned_off.json()["pull_enabled"] is False
    # Раньше входящую синхронизацию выключить было нельзя, хотя документы это обещали.
    assert [run.source_id for run in runs] == [sources["site"].id]


async def test_source_token_travels_with_the_request(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str | None] = []

    def capture(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get("authorization"))
        return httpx.Response(200, json={"accepted": [], "rejected": {}})

    monkeypatch.setenv("SITE_TOKEN", "secret-from-env")
    client = HttpSiteClient(
        "http://site", token=source_token("SITE_TOKEN"), transport=httpx.MockTransport(capture)
    )

    await client.push_interactions([])

    # Секрет берётся из окружения по имени, в базе лежит только имя переменной.
    assert seen == ["Bearer secret-from-env"]


async def test_foreign_matched_application_is_hidden_and_kept(
    client: AsyncClient, session: AsyncSession
) -> None:
    source = await source_of(session, SITE_NAME)
    await sync_source(session, source, FakeSite(site_records()))
    matched = await session.scalar(
        select(SiteApplication).where(SiteApplication.external_id == "site-1")
    )
    assert matched is not None
    # Запись ИТМО уходит КАМу другой команды: руководителю Роману она больше не видна.
    stranger = AppUser(email="stranger@example.com", full_name="Чужой КАМ", role="kam")
    session.add(stranger)
    await session.flush()
    record = await session.get(Interaction, matched.interaction_id)
    assert record is not None
    record.owner_user_id = stranger.id
    await session.commit()
    own = await find(client, ANNA_KAM, stage_code="signing")

    listed = await client.get("/api/v1/site-applications", headers=as_user(ROMAN_MANAGER))
    taken = await client.post(
        f"/api/v1/site-applications/{matched.id}/match",
        json={"interaction_id": own["id"]},
        headers=as_user(ROMAN_MANAGER),
    )

    # ФИО заявителя из чужой записи не показывается, а заявку нельзя увести к себе.
    assert "site-1" not in {item["external_id"] for item in listed.json()}
    assert "site-2" in {item["external_id"] for item in listed.json()}
    assert taken.status_code == 404


async def test_new_university_goes_to_the_team_that_works_with_universities(
    session: AsyncSession,
) -> None:
    source = await source_of(session, SITE_NAME)
    # Руководитель частных лиц без записей вузов: заявка вуза ему не достаётся.
    other = AppUser(email="b2c.boss@example.com", full_name="Руководитель B2C", role="manager")
    session.add(other)
    await session.flush()
    session.add(Team(name="Частные лица", manager_user_id=other.id))
    session.add(University(name="Новый университет", short_name="НУ", region="Москва"))
    # Строка Романа переезжает в конец таблицы: без ORDER BY первым нашёлся бы другой.
    await session.execute(
        update(AppUser).where(AppUser.email == ROMAN_MANAGER).values(full_name=AppUser.full_name)
    )
    await session.commit()
    record = ApplicationRecord(
        "site-nu", "Новый университет", "Веб-разработка", "Декан", None, datetime.now(UTC)
    )

    await sync_source(session, source, FakeSite([record]))

    application = await session.scalar(
        select(SiteApplication).where(SiteApplication.external_id == "site-nu")
    )
    assert application is not None
    created = await session.get(Interaction, application.interaction_id)
    assert created is not None
    owner = await session.get(AppUser, created.owner_user_id)
    assert owner is not None
    assert owner.email == ROMAN_MANAGER
