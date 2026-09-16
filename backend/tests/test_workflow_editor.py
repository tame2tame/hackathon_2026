"""Редактор процесса: черновик, правка, переименование и публикация с переносом записей."""

from typing import Any

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.interactions.models import Interaction, Transition
from app.modules.workflow.models import WorkflowTemplate, WorkflowVersion
from tests.api import find
from tests.users import ALINA_ADMIN, ANNA_KAM, ROMAN_MANAGER, as_user

WORKFLOWS = "/api/v1/workflows"
VERSIONS = "/api/v1/workflow-versions"


async def default_template(session: AsyncSession) -> WorkflowTemplate:
    template = await session.scalar(
        select(WorkflowTemplate).where(WorkflowTemplate.is_default.is_(True))
    )
    assert template is not None
    return template


async def make_draft(client: AsyncClient, template_id: str) -> dict[str, Any]:
    response = await client.post(
        f"{WORKFLOWS}/{template_id}/versions", headers=as_user(ROMAN_MANAGER)
    )
    assert response.status_code == 201, response.text
    draft: dict[str, Any] = response.json()
    return draft


async def test_kam_cannot_edit_the_process(client: AsyncClient) -> None:
    response = await client.post(
        WORKFLOWS, json={"name": "Свой процесс"}, headers=as_user(ANNA_KAM)
    )

    assert response.status_code == 403
    assert response.json()["code"] == "AUTH_FORBIDDEN"


async def test_template_name_is_unique(client: AsyncClient) -> None:
    first = await client.post(
        WORKFLOWS, json={"name": "Процесс для вузов"}, headers=as_user(ALINA_ADMIN)
    )
    second = await client.post(
        WORKFLOWS, json={"name": "Процесс для вузов"}, headers=as_user(ALINA_ADMIN)
    )

    assert first.status_code == 201
    assert second.status_code == 422
    assert second.json()["errors"] == [{"field": "name", "message": "Название занято"}]


async def test_draft_copies_the_published_version(
    client: AsyncClient, session: AsyncSession
) -> None:
    template = await default_template(session)

    draft = await make_draft(client, str(template.id))

    assert draft["status"] == "draft"
    assert draft["version_no"] == 2
    assert len(draft["stages"]) == 14
    assert draft["transitions"]
    # Нормы привязаны к коду этапа, поэтому в копии они на месте.
    signing = next(stage for stage in draft["stages"] if stage["code"] == "signing")
    assert signing["norm_days"] == 14


async def test_published_version_cannot_be_changed(
    client: AsyncClient, session: AsyncSession
) -> None:
    published = await session.scalar(
        select(WorkflowVersion).where(WorkflowVersion.status == "published")
    )
    assert published is not None

    response = await client.patch(
        f"{VERSIONS}/{published.id}",
        json={"transitions": []},
        headers=as_user(ROMAN_MANAGER),
    )

    assert response.status_code == 409
    assert response.json()["code"] == "WF_VERSION_NOT_DRAFT"


async def test_stage_can_be_renamed_in_a_published_version(
    client: AsyncClient, session: AsyncSession
) -> None:
    workflow = (await client.get(f"{WORKFLOWS}/default", headers=as_user(ANNA_KAM))).json()
    stage = next(item for item in workflow["stages"] if item["code"] == "signing")

    response = await client.patch(
        f"/api/v1/stages/{stage['id']}",
        json={"name": "Подписание договора"},
        headers=as_user(ROMAN_MANAGER),
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Подписание договора"
    card = await find(client, ANNA_KAM, stage_code="signing")
    assert card["stage"]["name"] == "Подписание договора"


async def test_draft_stages_and_rules_are_replaced(
    client: AsyncClient, session: AsyncSession
) -> None:
    template = await default_template(session)
    draft = await make_draft(client, str(template.id))

    response = await client.patch(
        f"{VERSIONS}/{draft['id']}",
        json={
            "stages": [
                {"code": "contact_search", "name": "Поиск", "position": 1, "kind": "start"},
                {"code": "signing", "name": "Подписание", "position": 2, "norm_days": 10},
                {"code": "classes", "name": "Занятия", "position": 3, "kind": "final"},
            ],
            "transitions": [
                {"from_code": "contact_search", "to_code": "signing"},
                {"from_code": "signing", "to_code": "classes", "requires_attachment": True},
            ],
        },
        headers=as_user(ROMAN_MANAGER),
    )

    assert response.status_code == 200
    body = response.json()
    assert [stage["code"] for stage in body["stages"]] == ["contact_search", "signing", "classes"]
    assert len(body["transitions"]) == 2
    assert next(s["norm_days"] for s in body["stages"] if s["code"] == "signing") == 10


async def test_unknown_stage_in_transitions_is_refused(
    client: AsyncClient, session: AsyncSession
) -> None:
    template = await default_template(session)
    draft = await make_draft(client, str(template.id))

    response = await client.patch(
        f"{VERSIONS}/{draft['id']}",
        json={"transitions": [{"from_code": "signing", "to_code": "нет_такого"}]},
        headers=as_user(ROMAN_MANAGER),
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


async def test_publish_needs_a_map_for_busy_stages(
    client: AsyncClient, session: AsyncSession
) -> None:
    template = await default_template(session)
    draft = await make_draft(client, str(template.id))
    # В новой версии нет этапа «Подписание», а на нём стоит демо-взаимодействие.
    await client.patch(
        f"{VERSIONS}/{draft['id']}",
        json={
            "stages": [
                {"code": "contact_search", "name": "Поиск", "position": 1, "kind": "start"},
                {"code": "work", "name": "Работа", "position": 2},
            ],
            "transitions": [{"from_code": "contact_search", "to_code": "work"}],
        },
        headers=as_user(ROMAN_MANAGER),
    )

    response = await client.post(
        f"{VERSIONS}/{draft['id']}/publish", json={}, headers=as_user(ROMAN_MANAGER)
    )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "WF_MIGRATION_MAP_INCOMPLETE"
    assert any(error["field"].startswith("migration_map.") for error in body["errors"])


async def test_publish_moves_open_interactions(client: AsyncClient, session: AsyncSession) -> None:
    template = await default_template(session)
    item = await find(client, ANNA_KAM, stage_code="signing")
    draft = await make_draft(client, str(template.id))
    await client.patch(
        f"{VERSIONS}/{draft['id']}",
        json={
            "stages": [
                {"code": "contact_search", "name": "Поиск", "position": 1, "kind": "start"},
                {"code": "work", "name": "Работа", "position": 2},
                {"code": "done", "name": "Готово", "position": 3, "kind": "final"},
            ],
            "transitions": [
                {"from_code": "contact_search", "to_code": "work"},
                {"from_code": "work", "to_code": "done"},
            ],
        },
        headers=as_user(ROMAN_MANAGER),
    )
    old_codes = ["contact_search", "communication", "meeting", "documents_exchange",
                 "documents_revision", "signing", "materials_transfer", "implementation_support",
                 "teacher_training", "curriculum_update", "classes", "docs_update",
                 "teacher_upskilling", "stage_control"]  # fmt: skip

    response = await client.post(
        f"{VERSIONS}/{draft['id']}/publish",
        json={"migration_map": {code: "work" for code in old_codes}},
        headers=as_user(ROMAN_MANAGER),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "published"
    moved = await session.get(Interaction, item["id"])
    assert moved is not None
    await session.refresh(moved)
    assert str(moved.workflow_version_id) == draft["id"]
    migration = await session.scalar(
        select(Transition).where(
            Transition.interaction_id == moved.id, Transition.source == "migration"
        )
    )
    assert migration is not None
    retired = await session.scalar(
        select(WorkflowVersion).where(
            WorkflowVersion.template_id == template.id, WorkflowVersion.version_no == 1
        )
    )
    assert retired is not None
    assert retired.status == "retired"
