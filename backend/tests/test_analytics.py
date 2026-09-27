"""Рейтинг востребованности и статистика процесса."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics import router as analytics_router
from app.modules.analytics.charts import render_charts
from app.modules.analytics.rating import DEFAULT_WEIGHTS, Entry, normalize_weights, rate
from app.modules.analytics.schemas import ChartOut
from app.modules.catalogs.models import CounterpartyGroup, Program, University
from app.modules.metrics.models import ProgramMetric
from app.modules.workflow.defaults import INDIVIDUALS_GROUP
from tests.test_workflow_editor import default_template, make_draft, publish
from tests.users import ALINA_ADMIN, ANNA_KAM, ROMAN_MANAGER, as_user

RATING = "/api/v1/analytics/rating"
DEVOPS = uuid.uuid4()
AI = uuid.uuid4()


def entry(name: str, direction: uuid.UUID, **values: float) -> Entry:
    return Entry(
        key=uuid.uuid4(),
        name=name,
        direction_id=direction,
        direction_name="Направление",
        values=values,
    )


def test_contributions_sum_to_the_score() -> None:
    rows = rate(
        [
            entry("Лучшая", DEVOPS, applications=100, students=80, streams=4),
            entry("Средняя", DEVOPS, applications=50, students=40, streams=2),
        ],
        DEFAULT_WEIGHTS,
    )

    for row in rows:
        assert abs(sum(item.contribution for item in row.contributions) - row.score) <= 0.1
    assert rows[0].name == "Лучшая"
    assert rows[0].score == 100.0


def test_missing_metric_redistributes_weights() -> None:
    [row] = rate([entry("Одна", DEVOPS, applications=10, students=5)], DEFAULT_WEIGHTS)

    assert row.missing_metrics == ["streams"]
    assert row.complete is False
    # Потоков нет: оставшиеся веса дают полный балл, а не 80 из 100.
    assert row.score == 100.0
    assert {item.metric for item in row.contributions} == {"applications", "students"}


def test_normalisation_happens_inside_a_direction() -> None:
    rows = rate(
        [
            entry("DevOps большая", DEVOPS, applications=1000, students=900, streams=10),
            entry("DevOps малая", DEVOPS, applications=100, students=90, streams=1),
            entry("ИИ малая", AI, applications=10, students=9, streams=1),
        ],
        DEFAULT_WEIGHTS,
    )

    by_name = {row.name: row for row in rows}
    # Маленькая программа в своём направлении лучшая, поэтому у неё 100 баллов.
    assert by_name["ИИ малая"].score == 100.0
    assert by_name["DevOps малая"].score == 10.0


def test_weights_must_sum_to_hundred() -> None:
    assert normalize_weights({"applications": 50, "students": 30, "streams": 20})

    with pytest.raises(ValueError, match="Сумма весов"):
        normalize_weights({"applications": 50, "students": 30, "streams": 30})


async def seed_metrics(session: AsyncSession) -> tuple[str, str]:
    """Две программы одного направления: у первой больше заявок, у второй — обучающихся.

    Нормирование идёт внутри направления, поэтому сравнивать имеет смысл только соседей
    по направлению — в демо-данных у каждого направления одна программа, вторую заводим тут.
    """
    month = datetime.now(UTC).date().replace(day=1)
    university = await session.scalar(select(University).limit(1))
    first = await session.scalar(select(Program).order_by(Program.name).limit(1))
    assert university is not None
    assert first is not None
    second = Program(direction_id=first.direction_id, name="Вторая программа направления")
    session.add(second)
    await session.flush()

    plan = (
        (first, {"applications": 100, "students": 20, "streams": 1}),
        (second, {"applications": 20, "students": 100, "streams": 4}),
    )
    for program, values in plan:
        for metric, value in values.items():
            session.add(
                ProgramMetric(
                    university_id=university.id,
                    program_id=program.id,
                    period_month=month,
                    metric=metric,
                    value=value,
                    source="manual",
                )
            )
    await session.commit()
    return first.name, second.name


async def test_weights_change_the_order(client: AsyncClient, session: AsyncSession) -> None:
    by_applications_name, by_students_name = await seed_metrics(session)
    today = datetime.now(UTC).date()
    params = {"period_from": str(today - timedelta(days=30)), "period_to": str(today)}

    by_applications = await client.get(
        RATING,
        params={**params, "w_applications": 80, "w_students": 10, "w_streams": 10},
        headers=as_user(ROMAN_MANAGER),
    )
    by_students = await client.get(
        RATING,
        params={**params, "w_applications": 10, "w_students": 80, "w_streams": 10},
        headers=as_user(ROMAN_MANAGER),
    )

    assert by_applications.status_code == 200
    # Когда вес заявок больше, первой идёт программа с заявками, и наоборот.
    assert by_applications.json()["rows"][0]["name"] == by_applications_name
    assert by_students.json()["rows"][0]["name"] == by_students_name


async def test_month_on_the_border_is_not_counted_twice(
    client: AsyncClient, session: AsyncSession
) -> None:
    await seed_metrics(session)
    month = datetime.now(UTC).date().replace(day=1)
    # Период начинается в середине месяца метрик: раньше предыдущий период заканчивался в том
    # же месяце, забирал те же метрики, и у каждой строки был «сдвиг 0» вместо «новая».
    params = {
        "period_from": str(month + timedelta(days=20)),
        "period_to": str(month + timedelta(days=40)),
    }

    response = await client.get(RATING, params=params, headers=as_user(ROMAN_MANAGER))

    assert response.status_code == 200
    assert response.json()["rows"]
    assert {row["place_change"] for row in response.json()["rows"]} == {None}


async def test_rating_returns_contributions_and_completeness(
    client: AsyncClient, session: AsyncSession
) -> None:
    await seed_metrics(session)

    response = await client.get(RATING, headers=as_user(ANNA_KAM))

    assert response.status_code == 200
    body = response.json()
    assert body["weights"] == DEFAULT_WEIGHTS
    row = body["rows"][0]
    assert abs(sum(item["contribution"] for item in row["contributions"]) - row["score"]) <= 0.1
    assert row["complete"] is True


async def test_broken_weights_are_refused(client: AsyncClient) -> None:
    response = await client.get(
        RATING,
        params={"w_applications": 50, "w_students": 30, "w_streams": 30},
        headers=as_user(ROMAN_MANAGER),
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


async def test_only_manager_changes_default_weights(client: AsyncClient) -> None:
    payload = {"w_applications": 50, "w_students": 30, "w_streams": 20}

    kam = await client.put(f"{RATING}/weights", json=payload, headers=as_user(ANNA_KAM))
    admin = await client.put(f"{RATING}/weights", json=payload, headers=as_user(ALINA_ADMIN))

    assert kam.status_code == 403
    assert admin.status_code == 200
    assert admin.json()["w_applications"] == 50


async def test_stats_return_charts(client: AsyncClient) -> None:
    funnel = await client.get("/api/v1/analytics/stats/funnel", headers=as_user(ALINA_ADMIN))
    durations = await client.get(
        "/api/v1/analytics/stats/stage-durations", headers=as_user(ALINA_ADMIN)
    )
    distribution = await client.get(
        "/api/v1/analytics/stats/distribution", headers=as_user(ALINA_ADMIN)
    )

    assert funnel.status_code == 200
    body = funnel.json()
    assert sum(body["values"]) == 6  # шесть демо-связок
    assert body["option"]["series"][0]["type"] == "bar"
    assert durations.status_code == 200
    assert distribution.json()["labels"]


async def test_kam_sees_the_funnel_of_own_records(client: AsyncClient) -> None:
    response = await client.get("/api/v1/analytics/stats/funnel", headers=as_user(ANNA_KAM))

    assert sum(response.json()["values"]) == 4


async def test_statistics_come_as_a_printable_file(client: AsyncClient) -> None:
    report = await client.get("/api/v1/analytics/stats/report", headers=as_user(ROMAN_MANAGER))
    by_kam = await client.get("/api/v1/analytics/stats/report", headers=as_user(ANNA_KAM))

    assert report.status_code == 200, report.text
    assert report.headers["content-type"] == "application/pdf"
    assert report.content.startswith(b"%PDF")
    # Диаграммы рисует сервер, поэтому файл заметно больше пустого PDF.
    assert len(report.content) > 3000
    assert (
        "Статистика" in report.headers["content-disposition"]
        or "%D0" in report.headers["content-disposition"]
    )
    # КАМ видит свою область: файл строится, но по его записям.
    assert by_kam.status_code == 200


async def test_printed_statistics_match_the_charts(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    printed: dict[str, object] = {}

    def spy(title: str, subtitle: str, charts: list[ChartOut]) -> bytes:
        printed.update(subtitle=subtitle, charts=charts)
        return render_charts(title, subtitle, charts)

    monkeypatch.setattr(analytics_router, "render_charts", spy)
    headers = as_user(ROMAN_MANAGER)
    await client.get("/api/v1/analytics/stats/report", headers=headers)
    on_screen = [
        (await client.get(f"/api/v1/analytics/stats/{name}", headers=headers)).json()
        for name in ("funnel", "stage-durations", "distribution")
    ]

    charts = printed["charts"]
    assert isinstance(charts, list)
    assert [(c.labels, c.values) for c in charts] == [
        (chart["labels"], chart["values"]) for chart in on_screen
    ]
    # Без группы воронка считается по вузам, а направления — по всем: подпись это говорит.
    assert printed["subtitle"] == (
        "Воронка и длительности — группа «Вузы (B2B)», направления — все группы"
    )


def test_long_labels_do_not_run_into_the_next_chart() -> None:
    long = ChartOut(
        title="Длинные подписи",
        labels=["Очень длинное название этапа процесса взаимодействия с вузом"] * 3,
        values=[1, 2, 3],
        option={},
    )

    assert render_charts("Т", "П", [long, long, long]).startswith(b"%PDF")


async def test_chart_page_survives_empty_data(client: AsyncClient, session: AsyncSession) -> None:
    group = await session.scalar(
        select(CounterpartyGroup).where(CounterpartyGroup.code == INDIVIDUALS_GROUP)
    )
    assert group is not None

    report = await client.get(
        "/api/v1/analytics/stats/report",
        params={"group_id": str(group.id)},
        headers=as_user(ALINA_ADMIN),
    )

    assert report.status_code == 200, report.text
    assert report.content.startswith(b"%PDF")


async def test_funnel_keeps_every_stage_and_skips_cancelled(client: AsyncClient) -> None:
    before = await client.get("/api/v1/analytics/stats/funnel", headers=as_user(ANNA_KAM))
    kfu = next(
        item
        for item in (
            await client.get(
                "/api/v1/interactions", params={"search": "КФУ"}, headers=as_user(ANNA_KAM)
            )
        ).json()["items"]
    )
    await client.put(
        f"/api/v1/interactions/{kfu['id']}/status",
        json={"status": "cancelled", "reason": "Ошибка", "expected_version": kfu["version"]},
        headers=as_user(ANNA_KAM),
    )
    after = await client.get("/api/v1/analytics/stats/funnel", headers=as_user(ANNA_KAM))

    # У КАМа раньше пропадали этапы без его записей: теперь все 14 этапов процесса на месте.
    assert len(before.json()["labels"]) == 14
    # Отменённая запись из воронки уходит.
    assert sum(after.json()["values"]) == sum(before.json()["values"]) - 1


async def test_stage_durations_survive_a_publication(
    client: AsyncClient, session: AsyncSession
) -> None:
    before = await client.get(
        "/api/v1/analytics/stats/stage-durations", headers=as_user(ALINA_ADMIN)
    )
    # Публикуем копию процесса без изменений: история переходов от этого не должна пропасть.
    draft = await make_draft(client, str((await default_template(session)).id))
    published = await publish(client, draft)
    after = await client.get(
        "/api/v1/analytics/stats/stage-durations", headers=as_user(ALINA_ADMIN)
    )

    assert published.status_code == 200, published.text
    assert before.json()["labels"]
    assert after.json() == before.json()
