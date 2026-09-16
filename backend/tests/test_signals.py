from collections import Counter

from httpx import AsyncClient

from tests.users import ALINA_ADMIN, MIKHAIL_KAM, ROMAN_MANAGER, as_user


async def test_demo_radar_matches_planted_problems(client: AsyncClient) -> None:
    response = await client.get("/api/v1/signals", headers=as_user(ALINA_ADMIN))

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 7
    assert Counter(s["kind"] for s in body["items"]) == {
        "stage_overdue": 2,
        "missing_document": 2,
        "license_expiring": 2,
        "inactivity": 1,
    }
    severities = [s["severity"] for s in body["items"]]
    assert severities == sorted(severities, key=["high", "medium", "low"].index)


async def test_signal_message_is_checkable(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/signals",
        params={"kind": "license_expiring", "search": "ИТМО"},
        headers=as_user(ALINA_ADMIN),
    )

    [signal] = response.json()["items"]
    assert signal["severity"] == "high"
    assert signal["evidence"]["days_left"] == 19
    assert "Д-2026/042" in signal["message"]
    assert signal["message"].endswith("через 19 дней.")


async def test_summary_builds_the_matrix_for_a_manager(client: AsyncClient) -> None:
    response = await client.get("/api/v1/signals/summary", headers=as_user(ROMAN_MANAGER))

    assert response.status_code == 200
    summary = response.json()
    assert summary["total"] == 7
    by_owner = {row["owner"]["full_name"]: row for row in summary["rows"]}
    assert by_owner["Анна Смирнова"]["total"] == 5
    assert by_owner["Михаил Волков"]["counts"]["missing_document"] == 1


async def test_summary_for_a_kam_holds_only_own_rows(client: AsyncClient) -> None:
    response = await client.get("/api/v1/signals/summary", headers=as_user(MIKHAIL_KAM))

    summary = response.json()
    assert [row["owner"]["full_name"] for row in summary["rows"]] == ["Михаил Волков"]
    assert summary["total"] == 2


async def test_kam_sees_only_own_signals(client: AsyncClient) -> None:
    response = await client.get("/api/v1/signals", headers=as_user(MIKHAIL_KAM))

    universities = {s["interaction"]["university"]["short_name"] for s in response.json()["items"]}
    assert universities == {"НГУ", "УрФУ"}
