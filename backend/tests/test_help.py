"""Встроенная справка: разделы по ролям и документ, собранный из них же."""

from pathlib import Path

from httpx import AsyncClient

from app.modules.help.service import topics
from scripts.export_help import render
from tests.users import ALINA_ADMIN, ANNA_KAM, ROMAN_MANAGER, as_user

HELP = "/api/v1/help"
GUIDE_PATH = Path(__file__).resolve().parents[2] / "docs" / "USER_GUIDE.md"


async def test_kam_sees_the_guide_without_the_admin_part(client: AsyncClient) -> None:
    for_kam = await client.get(HELP, headers=as_user(ANNA_KAM))
    for_admin = await client.get(HELP, headers=as_user(ALINA_ADMIN))
    admin_topic = await client.get(f"{HELP}/admin", headers=as_user(ANNA_KAM))

    assert for_kam.status_code == 200, for_kam.text
    slugs = [item["slug"] for item in for_kam.json()]
    assert slugs[0] == "start"
    assert "admin" not in slugs
    assert "admin" in [item["slug"] for item in for_admin.json()]
    # Чужой раздел не просто скрыт в списке — его нельзя открыть по прямой ссылке.
    assert admin_topic.status_code == 404


async def test_topic_returns_text(client: AsyncClient) -> None:
    radar = await client.get(f"{HELP}/radar", headers=as_user(ROMAN_MANAGER))
    unknown = await client.get(f"{HELP}/нет-такого", headers=as_user(ROMAN_MANAGER))

    body = radar.json()
    assert body["title"].startswith("Радар")
    assert "Просрочка этапа" in body["body"]
    assert unknown.status_code == 404
    assert unknown.json()["code"] == "NOT_FOUND"


async def test_help_needs_a_signed_in_user(client: AsyncClient) -> None:
    response = await client.get(HELP)

    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_REQUIRED"


def test_every_topic_is_filled() -> None:
    for topic in topics():
        assert topic.roles, topic.slug
        assert len(topic.summary) <= 120, topic.slug
        # Раздел без текста бесполезен: справка должна отвечать на вопрос, а не быть заголовком.
        assert len(topic.body) > 300, topic.slug


def test_guide_matches_the_built_in_help() -> None:
    assert GUIDE_PATH.exists(), "Нет docs/USER_GUIDE.md: выполните make help"
    assert GUIDE_PATH.read_text(encoding="utf-8") == render(), (
        "Справка изменилась: выполните make help и закоммитьте руководство"
    )


async def test_screenshots_are_served_from_the_help(client: AsyncClient) -> None:
    picture = await client.get(f"{HELP}/images/radar.png", headers=as_user(ANNA_KAM))
    unknown = await client.get(f"{HELP}/images/нет.png", headers=as_user(ANNA_KAM))
    traversal = await client.get(f"{HELP}/images/..%2F..%2Fmain.py", headers=as_user(ANNA_KAM))
    without_login = await client.get(f"{HELP}/images/radar.png")

    assert picture.status_code == 200, picture.text
    assert picture.headers["content-type"] == "image/png"
    assert picture.content.startswith(b"\x89PNG")
    assert unknown.status_code == 404
    assert traversal.status_code == 404
    assert without_login.status_code == 401


def test_guide_shows_the_same_screenshots() -> None:
    guide = GUIDE_PATH.read_text(encoding="utf-8")
    images = {topic.slug for topic in topics() if "/api/v1/help/images/" in topic.body}

    assert images, "в справке нет ни одного скриншота"
    # В продукте картинка приходит по адресу API, в документе — файлом из репозитория.
    assert "../backend/app/help/images/radar.png" in guide
    assert "/api/v1/help/images/" not in guide
