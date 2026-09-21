"""Встроенная справка: разделы руководства лежат рядом с кодом и отдаются по API.

Жюри просило руководства «лучше встроенные в продукт», поэтому текст живёт в репозитории
в `app/help/*.md` и оттуда попадает и в интерфейс, и в документ `docs/USER_GUIDE.md`,
который собирает `scripts/export_help.py`. Один источник — значит, интерфейс и документ
не расходятся.

Раздел — обычный Markdown с заголовком в начале файла:

    ---
    slug: radar
    title: Радар: что означают сигналы
    roles: kam, manager, admin
    summary: Четыре сигнала, пороги и что с ними делать
    ---
"""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.core.errors import AppError, ErrorCode
from app.core.roles import Role
from app.modules.help.schemas import HelpTopicOut, HelpTopicRef

HELP_DIR = Path(__file__).resolve().parents[2] / "help"
SEPARATOR = "---"
REQUIRED = ("slug", "title", "summary", "roles")


@dataclass(frozen=True, slots=True)
class Topic:
    slug: str
    title: str
    summary: str
    roles: frozenset[str]
    body: str
    order: str

    def ref(self) -> HelpTopicRef:
        return HelpTopicRef(slug=self.slug, title=self.title, summary=self.summary)

    def out(self) -> HelpTopicOut:
        return HelpTopicOut(slug=self.slug, title=self.title, summary=self.summary, body=self.body)


def _parse(path: Path) -> Topic:
    text = path.read_text(encoding="utf-8")
    if not text.startswith(SEPARATOR):
        raise ValueError(f"{path.name}: нет заголовка раздела")
    _, header, body = text.split(f"{SEPARATOR}\n", 2)
    fields: dict[str, str] = {}
    for line in header.splitlines():
        if not line.strip():
            continue
        name, _, value = line.partition(":")
        fields[name.strip()] = value.strip()
    missing = [name for name in REQUIRED if not fields.get(name)]
    if missing:
        raise ValueError(f"{path.name}: не заполнено {', '.join(missing)}")
    roles = {role.strip() for role in fields["roles"].split(",") if role.strip()}
    unknown = roles - {role.value for role in Role}
    if unknown:
        raise ValueError(f"{path.name}: неизвестные роли {', '.join(sorted(unknown))}")
    return Topic(
        slug=fields["slug"],
        title=fields["title"],
        summary=fields["summary"],
        roles=frozenset(roles),
        body=body.strip(),
        order=path.name,
    )


@lru_cache
def topics() -> tuple[Topic, ...]:
    """Разделы в порядке имён файлов: номер в имени задаёт порядок в оглавлении."""
    found = tuple(_parse(path) for path in sorted(HELP_DIR.glob("*.md")))
    slugs = [topic.slug for topic in found]
    if len(set(slugs)) != len(slugs):
        raise ValueError("Повторяющийся slug раздела справки")
    return found


def list_topics(role: Role) -> list[HelpTopicRef]:
    return [topic.ref() for topic in topics() if role.value in topic.roles]


def get_topic(role: Role, slug: str) -> HelpTopicOut:
    for topic in topics():
        if topic.slug == slug and role.value in topic.roles:
            return topic.out()
    raise AppError(ErrorCode.NOT_FOUND, "Раздел справки не найден.")
