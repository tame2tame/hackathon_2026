"""Нормы этапов: подсказки по истории, ручная правка и принятие подсказки."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.radar.norms import MIN_OBSERVATIONS, percentile, suggest_norm
from app.modules.workflow.service import refresh_suggestions
from tests.users import ANNA_KAM, ROMAN_MANAGER, as_user

NORMS = "/api/v1/workflows/default/norms"


def test_percentile_takes_the_nearest_rank() -> None:
    assert percentile([1, 2, 3, 4, 5], 0.8) == 4
    assert percentile([10], 0.8) == 10
    with pytest.raises(ValueError, match="наблюдение"):
        percentile([], 0.8)


def test_suggestion_needs_enough_history() -> None:
    assert suggest_norm([5] * (MIN_OBSERVATIONS - 1)) is None

    suggestion = suggest_norm([4, 6, 8, 10, 30])

    assert suggestion is not None
    # Ближайший ранг: в 10 дней укладываются 4 наблюдения из 5, поэтому выброс в 30 не берётся.
    assert suggestion.median_days == 8
    assert suggestion.percentile_days == 10
    assert suggestion.sample_size == 5


async def test_norms_list_shows_every_stage_with_norm(client: AsyncClient) -> None:
    response = await client.get(NORMS, headers=as_user(ANNA_KAM))

    assert response.status_code == 200
    norms = response.json()
    signing = next(norm for norm in norms if norm["stage_code"] == "signing")
    assert (signing["norm_days"], signing["source"]) == (14, "manual")
    assert signing["stage_name"] == "Подписание"


async def test_kam_cannot_change_norm(client: AsyncClient) -> None:
    response = await client.put(
        f"{NORMS}/signing", json={"norm_days": 30}, headers=as_user(ANNA_KAM)
    )

    assert response.status_code == 403
    assert response.json()["code"] == "AUTH_FORBIDDEN"


async def test_manager_sets_norm_manually(client: AsyncClient) -> None:
    response = await client.put(
        f"{NORMS}/signing", json={"norm_days": 21}, headers=as_user(ROMAN_MANAGER)
    )

    assert response.status_code == 200
    assert (response.json()["norm_days"], response.json()["source"]) == (21, "manual")


async def test_norm_out_of_range_is_refused(client: AsyncClient) -> None:
    response = await client.put(
        f"{NORMS}/signing", json={"norm_days": 0}, headers=as_user(ROMAN_MANAGER)
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


async def test_suggestion_is_refused_until_history_is_enough(client: AsyncClient) -> None:
    response = await client.post(
        f"{NORMS}/stage_control/accept-suggestion", headers=as_user(ROMAN_MANAGER)
    )

    assert response.status_code in {404, 422}


async def test_suggestion_from_history_can_be_accepted(
    client: AsyncClient, session: AsyncSession
) -> None:
    updated = await refresh_suggestions(session)
    await session.commit()
    assert updated > 0

    norms = (await client.get(NORMS, headers=as_user(ROMAN_MANAGER))).json()
    suggested = next(norm for norm in norms if norm["suggested_percentile_days"] is not None)

    accepted = await client.post(
        f"{NORMS}/{suggested['stage_code']}/accept-suggestion", headers=as_user(ROMAN_MANAGER)
    )

    assert accepted.status_code == 200
    body = accepted.json()
    assert body["source"] == "suggested"
    assert body["norm_days"] == suggested["suggested_percentile_days"]
    assert body["sample_size"] >= MIN_OBSERVATIONS
