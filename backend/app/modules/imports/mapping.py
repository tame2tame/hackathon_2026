"""Соответствие колонок выгрузки заказчика полям модели (ARCHITECTURE.md, раздел 3)."""

from collections.abc import Sequence
from enum import StrEnum


class ImportField(StrEnum):
    UNIVERSITY = "university"
    VENDOR = "vendor"
    PRODUCT = "product"
    CONTRACT_NUMBER = "contract_number"
    LICENSE_SIGNED_AT = "license_signed_at"
    LICENSE_VALID_UNTIL = "license_valid_until"
    TRANSFER_STATUS = "transfer_status"
    MANAGER = "manager"
    UNIVERSITY_CONTACTS = "university_contacts"
    COMMENT = "comment"


# Без этих трёх колонок нельзя определить взаимодействие: вуз × программа × продукт.
REQUIRED_FIELDS: tuple[ImportField, ...] = (
    ImportField.UNIVERSITY,
    ImportField.VENDOR,
    ImportField.PRODUCT,
)

# Нормализованные варианты заголовков: первый — как в файле заказчика.
HEADER_HINTS: dict[ImportField, tuple[str, ...]] = {
    ImportField.UNIVERSITY: ("названиевуза", "вуз", "университет", "наименованиевуза"),
    ImportField.VENDOR: ("вендор", "производитель", "правообладатель"),
    ImportField.PRODUCT: ("по", "продукт", "названиепо", "программноеобеспечение"),
    ImportField.CONTRACT_NUMBER: ("номердоговора", "договор", "номерлицензии"),
    ImportField.LICENSE_SIGNED_AT: ("подписаниелицензии", "датаподписания", "подписандоговор"),
    ImportField.LICENSE_VALID_UNTIL: ("срокдействиялицензии", "срокдействия", "лицензиядо"),
    ImportField.TRANSFER_STATUS: ("статуспопередаче", "статуспередачи", "статус"),
    ImportField.MANAGER: ("фиоменеджера", "менеджер", "ответственныйменеджер", "кам"),
    ImportField.UNIVERSITY_CONTACTS: ("ответственныеотвуза", "контактывуза", "контактноелицо"),
    ImportField.COMMENT: ("комментарий", "примечание"),
}

# «Статус по передаче» из файла → этап процесса. Неизвестное значение оставляет этап начальным.
TRANSFER_STATUS_STAGES: dict[str, str] = {
    "новый": "contact_search",
    "впоиске": "contact_search",
    "вработе": "communication",
    "переговоры": "communication",
    "встреча": "meeting",
    "обмендокументами": "documents_exchange",
    "наподписании": "signing",
    "подписан": "signing",
    "подписано": "signing",
    "передано": "materials_transfer",
    "передан": "materials_transfer",
    "внедрение": "implementation_support",
    "внедрено": "implementation_support",
    "обучениепреподавателей": "teacher_training",
    "обучение": "teacher_training",
    "ведутсязанятия": "classes",
    "занятия": "classes",
}


def normalize(value: str) -> str:
    """Без регистра, пробелов и знаков: «Название ВУЗа» и «название вуза » — одно и то же."""
    return "".join(ch for ch in value.casefold() if ch.isalnum())


def short_name(name: str) -> str:
    """Сокращение вуза: аббревиатура из заглавных букв, иначе первое слово."""
    letters = "".join(ch for ch in name if ch.isupper())
    if 2 <= len(letters) <= 12:
        return letters
    return name.split(",")[0].split()[0][:60] if name.split() else name[:60]


def suggest(headers: Sequence[str]) -> dict[str, str]:
    """Поле модели → заголовок файла. Точное совпадение заголовка важнее частичного."""
    normalized = {header: normalize(header) for header in headers if header.strip()}
    suggestion: dict[str, str] = {}
    taken: set[str] = set()

    for exact_pass in (True, False):
        for field, hints in HEADER_HINTS.items():
            if field.value in suggestion:
                continue
            for header, norm in normalized.items():
                if header in taken:
                    continue
                matched = norm in hints if exact_pass else any(hint in norm for hint in hints)
                if matched:
                    suggestion[field.value] = header
                    taken.add(header)
                    break
    return suggestion


def missing_required(column_map: dict[str, str]) -> list[str]:
    """Поля, без которых импорт не имеет смысла."""
    return [field.value for field in REQUIRED_FIELDS if not column_map.get(field.value)]


def stage_for_status(value: str | None) -> str | None:
    if not value:
        return None
    return TRANSFER_STATUS_STAGES.get(normalize(value))
