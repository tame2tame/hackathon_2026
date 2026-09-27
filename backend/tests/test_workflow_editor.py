"""Редактор процесса: черновик, правка, переименование и публикация с переносом записей."""

from itertools import pairwise
from typing import Any

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
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
        headers=as_user(ALINA_ADMIN),
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


@pytest.mark.parametrize(
    ("patch", "message"),
    [
        (
            {
                "stages": [
                    {"code": "a", "name": "А", "position": 1, "kind": "start"},
                    {"code": "b", "name": "Б", "position": 1, "kind": "final"},
                ]
            },
            "Номер этапа должен быть уникален",
        ),
        (
            {
                "transitions": [
                    {"from_code": "contact_search", "to_code": "signing"},
                    {"from_code": "contact_search", "to_code": "signing"},
                ]
            },
            "Переход повторяется",
        ),
        (
            {"transitions": [{"from_code": "signing", "to_code": "signing"}]},
            "Этап перехода совпадает",
        ),
    ],
)
async def test_broken_draft_is_explained_not_crashed(
    client: AsyncClient, session: AsyncSession, patch: dict[str, Any], message: str
) -> None:
    template = await default_template(session)
    draft = await make_draft(client, str(template.id))

    response = await client.patch(
        f"{VERSIONS}/{draft['id']}", json=patch, headers=as_user(ROMAN_MANAGER)
    )

    # Раньше повтор доходил до уникального индекса и возвращал 500.
    assert response.status_code == 422
    assert response.json()["errors"][0]["message"] == message


async def test_manager_cannot_rename_a_stage(client: AsyncClient) -> None:
    workflow = (await client.get(f"{WORKFLOWS}/default", headers=as_user(ANNA_KAM))).json()
    stage = next(item for item in workflow["stages"] if item["code"] == "signing")

    response = await client.patch(
        f"/api/v1/stages/{stage['id']}",
        json={"name": "Подписание договора"},
        headers=as_user(ROMAN_MANAGER),
    )

    assert response.status_code == 403
    assert response.json()["code"] == "AUTH_FORBIDDEN"


async def draft_without(
    client: AsyncClient,
    session: AsyncSession,
    removed: set[str],
    renamed: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Черновик базового процесса без указанных этапов; остальные идут подряд друг за другом."""
    template = await default_template(session)
    draft = await make_draft(client, str(template.id))
    kept = [stage for stage in draft["stages"] if stage["code"] not in removed]
    stages = [
        {
            "code": stage["code"],
            "name": (renamed or {}).get(stage["code"], stage["name"]),
            "position": position,
            "kind": stage["kind"],
        }
        for position, stage in enumerate(kept, start=1)
    ]
    transitions = [{"from_code": a["code"], "to_code": b["code"]} for a, b in pairwise(kept)]
    response = await client.patch(
        f"{VERSIONS}/{draft['id']}",
        json={"stages": stages, "transitions": transitions},
        headers=as_user(ROMAN_MANAGER),
    )
    assert response.status_code == 200, response.text
    return draft


async def publish(
    client: AsyncClient,
    draft: dict[str, Any],
    migration_map: dict[str, str] | None = None,
    email: str = ROMAN_MANAGER,
) -> Response:
    return await client.post(
        f"{VERSIONS}/{draft['id']}/publish",
        json={"migration_map": migration_map or {}},
        headers=as_user(email),
    )


async def test_removed_stage_moves_records_to_the_previous_stage(
    client: AsyncClient, session: AsyncSession
) -> None:
    kfu = await find(client, ANNA_KAM, stage_code="meeting")
    draft = await draft_without(client, session, {"meeting"})

    response = await publish(client, draft)

    assert response.status_code == 200, response.text
    moved = await find(client, ANNA_KAM, stage_code="communication")
    assert moved["id"] == kfu["id"]
    # Этап сменился не по вине КАМа: дни на этапе считаются заново.
    assert moved["days_on_stage"] == 0
    card = (await client.get(f"/api/v1/interactions/{kfu['id']}", headers=as_user(ANNA_KAM))).json()
    assert card["history"][0]["source"] == "migration"
    assert card["history"][0]["comment"] == (
        "Этап «Встреча» удалён из процесса: запись перенесена на «Коммуникация»"
    )
    # Записи на оставшихся этапах стоят где стояли.
    assert (await find(client, ANNA_KAM, stage_code="signing"))["stage"]["name"] == "Подписание"


async def test_records_move_forward_when_no_earlier_stage_is_left(
    client: AsyncClient, session: AsyncSession
) -> None:
    kfu = await find(client, ANNA_KAM, stage_code="meeting")
    draft = await draft_without(client, session, {"contact_search", "communication", "meeting"})

    response = await publish(client, draft)

    assert response.status_code == 200, response.text
    assert (await find(client, ANNA_KAM, stage_code="documents_exchange"))["id"] == kfu["id"]


async def test_migration_map_beats_the_neighbour(
    client: AsyncClient, session: AsyncSession
) -> None:
    kfu = await find(client, ANNA_KAM, stage_code="meeting")
    draft = await draft_without(client, session, {"meeting"})

    response = await publish(client, draft, {"meeting": "documents_exchange"})

    assert response.status_code == 200, response.text
    assert (await find(client, ANNA_KAM, stage_code="documents_exchange"))["id"] == kfu["id"]


async def test_map_to_a_missing_stage_is_refused(
    client: AsyncClient, session: AsyncSession
) -> None:
    draft = await draft_without(client, session, {"meeting"})

    response = await publish(client, draft, {"meeting": "нет_такого"})

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "WF_MIGRATION_MAP_INCOMPLETE"
    assert body["errors"] == [
        {"field": "migration_map.meeting", "message": "Нужен этап новой схемы"}
    ]


async def test_preview_shows_what_publishing_will_do(
    client: AsyncClient, session: AsyncSession
) -> None:
    draft = await draft_without(client, session, {"meeting"})

    preview = await client.post(
        f"{VERSIONS}/{draft['id']}/publish-preview", json={}, headers=as_user(ROMAN_MANAGER)
    )

    assert preview.status_code == 200, preview.text
    body = preview.json()
    assert body["renamed"] == []
    assert body["added"] == []
    assert body["requires_admin"] is False
    assert body["moves"] == [
        {
            "from_code": "meeting",
            "from_name": "Встреча",
            "stage_removed": True,
            "open_interactions": 1,
            "to_code": "communication",
            "to_name": "Коммуникация",
            "automatic": True,
        }
    ]
    # Предпросмотр ничего не меняет: запись ещё на встрече.
    assert (await find(client, ANNA_KAM, stage_code="meeting"))["stage"]["code"] == "meeting"

    response = await publish(client, draft)

    assert response.status_code == 200
    migrated = await session.scalar(
        select(func.count()).select_from(Transition).where(Transition.source == "migration")
    )
    assert migrated == body["moved_interactions"] == 6


async def test_renaming_draft_is_published_by_an_admin(
    client: AsyncClient, session: AsyncSession
) -> None:
    draft = await draft_without(client, session, set(), renamed={"signing": "Подписание договора"})

    preview = await client.post(
        f"{VERSIONS}/{draft['id']}/publish-preview", json={}, headers=as_user(ROMAN_MANAGER)
    )
    by_manager = await publish(client, draft)
    by_admin = await publish(client, draft, email=ALINA_ADMIN)

    assert preview.json()["requires_admin"] is True
    assert preview.json()["renamed"] == [
        {"code": "signing", "old_name": "Подписание", "new_name": "Подписание договора"}
    ]
    assert by_manager.status_code == 403
    assert by_manager.json()["code"] == "AUTH_FORBIDDEN"
    assert by_admin.status_code == 200
    assert (await find(client, ANNA_KAM, stage_code="signing"))["stage"]["name"] == (
        "Подписание договора"
    )


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

    # Черновик переименовывает «Поиск контактов» в «Поиск», поэтому публикует администратор.
    response = await client.post(
        f"{VERSIONS}/{draft['id']}/publish",
        json={"migration_map": {code: "work" for code in old_codes}},
        headers=as_user(ALINA_ADMIN),
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


async def test_stage_name_cannot_hide_a_line_break(
    client: AsyncClient, session: AsyncSession
) -> None:
    workflow = (await client.get(f"{WORKFLOWS}/default", headers=as_user(ANNA_KAM))).json()
    stage = next(item for item in workflow["stages"] if item["code"] == "signing")

    response = await client.patch(
        f"/api/v1/stages/{stage['id']}",
        json={"name": "Подписание\nX-Injected: 1"},
        headers=as_user(ALINA_ADMIN),
    )

    # Название этапа попадает в тему письма-уведомления: перенос строки туда пускать нельзя.
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


async def test_process_has_one_draft_at_a_time(client: AsyncClient, session: AsyncSession) -> None:
    template = await default_template(session)

    first = await make_draft(client, str(template.id))
    second = await make_draft(client, str(template.id))
    drafts = await session.scalar(
        select(func.count())
        .select_from(WorkflowVersion)
        .where(WorkflowVersion.template_id == template.id, WorkflowVersion.status == "draft")
    )

    # Второе «начать изменения» открывает тот же черновик, а не параллельный.
    assert second["id"] == first["id"]
    assert drafts == 1


async def test_database_refuses_a_second_published_scheme(session: AsyncSession) -> None:
    template = await default_template(session)
    latest = await session.scalar(
        select(func.max(WorkflowVersion.version_no)).where(
            WorkflowVersion.template_id == template.id
        )
    )
    assert latest is not None

    # Даже если код ошибётся, база не даст процессу две действующие схемы.
    extra = WorkflowVersion(template_id=template.id, version_no=latest + 1, status="published")
    savepoint = await session.begin_nested()
    session.add(extra)
    with pytest.raises(IntegrityError):
        await session.flush()
    await savepoint.rollback()
