"""События: досылка пропущенного по курсору и область видимости потока."""

import uuid

from httpx import AsyncClient

from app.core.events import (
    INTERACTION_TRANSITIONED,
    MESSAGE_CREATED,
    REPORT_UPDATED,
    SIGNAL_RESOLVED,
    Event,
    MemoryEventBus,
    get_event_bus,
)
from app.core.roles import Role
from app.core.security import CurrentUser
from app.modules.events.router import visible
from tests.api import find, stage_id, upload_pdf
from tests.users import ANNA_KAM, as_user

ANNA = uuid.uuid4()
MIKHAIL = uuid.uuid4()
TEAM = uuid.uuid4()


def user(role: Role, user_id: uuid.UUID, team_id: uuid.UUID | None = None) -> CurrentUser:
    return CurrentUser(
        id=user_id, email="x@example.com", full_name="Тест", role=role, team_id=team_id
    )


def event(owner: uuid.UUID | None) -> Event:
    return Event("1", INTERACTION_TRANSITIONED, {"interaction_id": "x"}, owner_user_id=owner)


def test_kam_sees_only_own_events() -> None:
    kam = user(Role.KAM, ANNA)

    assert visible(event(ANNA), kam, set()) is True
    assert visible(event(MIKHAIL), kam, set()) is False
    # Общие события — импорт, отчёты — КАМу не адресованы.
    assert visible(event(None), kam, set()) is False


def test_manager_sees_the_whole_team() -> None:
    manager = user(Role.MANAGER, uuid.uuid4(), TEAM)

    assert visible(event(MIKHAIL), manager, {MIKHAIL}) is True
    assert visible(event(MIKHAIL), manager, set()) is False
    assert visible(event(None), manager, set()) is True


def test_admin_sees_everything() -> None:
    admin = user(Role.ADMIN, uuid.uuid4())

    assert visible(event(MIKHAIL), admin, set()) is True
    assert visible(event(None), admin, set()) is True


async def test_reader_gets_what_it_missed() -> None:
    bus = MemoryEventBus()
    _, cursor = await bus.read(None, 1)

    await bus.publish(INTERACTION_TRANSITIONED, {"n": 1}, owner_user_id=ANNA)
    await bus.publish(SIGNAL_RESOLVED, {"n": 2}, owner_user_id=ANNA)

    missed, cursor = await bus.read(cursor, 1)
    assert [item.payload["n"] for item in missed] == [1, 2]

    # Курсор дошёл до конца: новых событий нет, читатель получает пульс.
    empty, _ = await bus.read(cursor, 1)
    assert empty == []


async def test_transition_publishes_an_event(client: AsyncClient) -> None:
    bus = get_event_bus()
    _, cursor = await bus.read(None, 1)
    item = await find(client, ANNA_KAM, stage_code="signing")
    target = await stage_id(client, "materials_transfer")
    attachment = await upload_pdf(client, ANNA_KAM, item["id"], "signed_contract")

    await client.post(
        f"/api/v1/interactions/{item['id']}/transitions",
        json={
            "to_stage_id": target,
            "comment": "Договор подписан",
            "expected_version": 1,
            "attachment_ids": [attachment["id"]],
        },
        headers=as_user(ANNA_KAM),
    )

    events, _ = await bus.read(cursor, 1)
    kinds = [event.kind for event in events]
    assert INTERACTION_TRANSITIONED in kinds
    transitioned = next(event for event in events if event.kind == INTERACTION_TRANSITIONED)
    assert transitioned.payload["to_stage_code"] == "materials_transfer"
    assert transitioned.owner_user_id is not None


def test_correspondence_is_personal_even_for_the_manager_and_admin() -> None:
    manager = user(Role.MANAGER, uuid.uuid4(), TEAM)
    admin = user(Role.ADMIN, uuid.uuid4())
    recipient = user(Role.KAM, MIKHAIL, TEAM)
    message = Event("1", MESSAGE_CREATED, {"message_id": "m"}, owner_user_id=MIKHAIL)

    # Руководитель команды адресата раньше видел, кто и кому пишет, — теперь нет.
    assert visible(message, recipient, set()) is True
    assert visible(message, manager, {MIKHAIL}) is False
    assert visible(message, admin, set()) is False


def test_access_rules_decide_for_events_about_a_record() -> None:
    record = uuid.uuid4()
    admin = user(Role.ADMIN, uuid.uuid4())
    kam = user(Role.KAM, ANNA)
    about_record = Event(
        "1", INTERACTION_TRANSITIONED, {"interaction_id": str(record)}, owner_user_id=ANNA
    )

    # Запрет администратора убрал запись из области видимости: событие о ней тоже не приходит.
    assert visible(about_record, kam, set(), allowed=set()) is False
    assert visible(about_record, kam, set(), allowed={record}) is True
    assert visible(about_record, admin, set(), allowed=set()) is False


def test_report_progress_goes_to_its_author() -> None:
    manager = user(Role.MANAGER, uuid.uuid4(), TEAM)
    report = Event("1", REPORT_UPDATED, {"report_id": "r"}, owner_user_id=ANNA)

    assert visible(report, user(Role.KAM, ANNA), set()) is True
    assert visible(report, manager, {ANNA}) is False
