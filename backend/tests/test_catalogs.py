import pytest
from httpx import AsyncClient

from tests.users import ALINA_ADMIN, ANNA_KAM, MIKHAIL_KAM, ROMAN_MANAGER, as_user


@pytest.mark.parametrize(
    ("email", "role", "scope"),
    [(ANNA_KAM, "kam", "own"), (ROMAN_MANAGER, "manager", "team"), (ALINA_ADMIN, "admin", "all")],
)
async def test_me_reports_role_and_scope(
    client: AsyncClient, email: str, role: str, scope: str
) -> None:
    response = await client.get("/api/v1/me", headers=as_user(email))

    assert response.status_code == 200
    body = response.json()
    assert (body["role"], body["scope"]) == (role, scope)


@pytest.mark.parametrize(
    ("email", "expected"),
    [
        (ANNA_KAM, {"ИТМО", "КФУ", "МГТУ", "СПбПУ"}),
        (MIKHAIL_KAM, {"НГУ", "УрФУ"}),
        (ROMAN_MANAGER, {"ИТМО", "КФУ", "МГТУ", "НГУ", "СПбПУ", "УрФУ"}),
    ],
)
async def test_universities_follow_scope(
    client: AsyncClient, email: str, expected: set[str]
) -> None:
    response = await client.get("/api/v1/universities", headers=as_user(email))

    assert response.status_code == 200
    assert {u["short_name"] for u in response.json()["items"]} == expected


async def test_university_outside_scope_is_not_found(client: AsyncClient) -> None:
    admin_list = await client.get(
        "/api/v1/universities", params={"search": "УрФУ"}, headers=as_user(ALINA_ADMIN)
    )
    urfu_id = admin_list.json()["items"][0]["id"]

    response = await client.get(f"/api/v1/universities/{urfu_id}", headers=as_user(ANNA_KAM))

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


async def test_default_workflow_has_fourteen_stages(client: AsyncClient) -> None:
    response = await client.get("/api/v1/workflows/default", headers=as_user(ANNA_KAM))

    assert response.status_code == 200
    body = response.json()
    stages = body["stages"]
    assert len(stages) == 14
    assert stages[0]["code"] == "contact_search"
    assert stages[-1]["kind"] == "final"
    by_id = {s["id"]: s["code"] for s in stages}
    pairs = {(by_id[t["from_stage_id"]], by_id[t["to_stage_id"]]) for t in body["transitions"]}
    assert ("documents_exchange", "signing") in pairs
    # У каждого перехода вперёд есть возврат на шаг назад.
    assert ("signing", "documents_exchange") in pairs
    assert len(pairs) == 28
