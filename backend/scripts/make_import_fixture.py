"""Фикстура импорта: выгрузка заказчика на 30 строк.

Пересоздать файл: `python -m scripts.make_import_fixture`. Тот же генератор вызывают тесты,
поэтому даты лицензий всегда считаются от переданного дня.
"""

import io
import random
from datetime import date, timedelta
from pathlib import Path

from openpyxl import Workbook

HEADERS = (
    "Название ВУЗа",
    "Вендор",
    "ПО",
    "Номер договора",
    "Подписание лицензии",
    "Срок действия лицензии",
    "Статус по передаче",
    "ФИО Менеджера",
    "Ответственные от ВУЗа",
    "Комментарий",
)

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "import_demo.xlsx"

UNIVERSITIES = (
    "Московский физико-технический институт",
    "Высшая школа экономики",
    "Российский университет дружбы народов",
    "Томский политехнический университет",
    "Южный федеральный университет",
    "Самарский университет",
    "Нижегородский университет имени Лобачевского",
    "Пермский политехнический университет",
    "Воронежский государственный университет",
    "Дальневосточный федеральный университет",
    "Сибирский федеральный университет",
    "Балтийский федеральный университет",
    "Северный арктический федеральный университет",
    "Тюменский государственный университет",
    "Саратовский государственный университет",
    "Волгоградский государственный университет",
    "Ярославский государственный университет",
    "Иркутский государственный университет",
    "Омский государственный технический университет",
    "Челябинский государственный университет",
    "Кубанский государственный университет",
    "Белгородский государственный университет",
    "Тульский государственный университет",
    "Рязанский радиотехнический университет",
    "Ульяновский государственный университет",
    "Курский государственный университет",
    "Алтайский государственный университет",
    "Мурманский арктический университет",
    "Псковский государственный университет",
    "Тверской государственный университет",
)

# ПО из справочника: у этих продуктов есть программа по умолчанию.
KNOWN_PRODUCTS = (
    ("Базис", "Базис"),
    ("Открытая мобильная платформа", "ОС Аврора"),
    ("Loginom", "Loginom"),
    ("Акола", "Акола"),
)
# ПО, которого в справочнике нет: предпросмотр попросит выбрать программу.
UNKNOWN_PRODUCTS = (
    ("Ред Софт", "РЕД ОС"),
    ("Новые облачные технологии", "МойОфис"),
    ("Астра Линукс", "Astra Linux"),
)

KNOWN_MANAGERS = ("Анна Смирнова", "Михаил Волков")
UNKNOWN_MANAGER = "Пётр Сидоров"

STATUSES = (
    "В работе",
    "Встреча",
    "Обмен документами",
    "На подписании",
    "Передано",
    "Обучение",
    "Ведутся занятия",
)

CONTACTS = ("Ольга Кузнецова", "Сергей Иванов", "Мария Петрова", "Дмитрий Орлов")

EXPIRING_ROWS = 5
CONFLICT_ROWS = 2
NEEDS_PROGRAM_ROWS = 3
TOTAL_ROWS = 30


def _rows(base_day: date) -> list[tuple[str, ...]]:
    """Строки выгрузки: 5 с истекающей лицензией, 2 с чужим менеджером, 3 с незнакомым ПО."""
    rng = random.Random(2026)  # noqa: S311 — тестовые данные, а не криптография
    rows: list[tuple[str, ...]] = []
    for index, university in enumerate(UNIVERSITIES[:TOTAL_ROWS]):
        expiring = index < EXPIRING_ROWS
        conflict = EXPIRING_ROWS <= index < EXPIRING_ROWS + CONFLICT_ROWS
        needs_program = (
            EXPIRING_ROWS + CONFLICT_ROWS
            <= index
            < EXPIRING_ROWS + CONFLICT_ROWS + NEEDS_PROGRAM_ROWS
        )

        if needs_program:
            vendor, product = UNKNOWN_PRODUCTS[index % len(UNKNOWN_PRODUCTS)]
        else:
            vendor, product = KNOWN_PRODUCTS[index % len(KNOWN_PRODUCTS)]
        manager = UNKNOWN_MANAGER if conflict else KNOWN_MANAGERS[index % len(KNOWN_MANAGERS)]

        days_left = rng.randint(7, 29) if expiring else rng.randint(200, 900)
        valid_until = base_day + timedelta(days=days_left)
        signed_at = valid_until - timedelta(days=365)
        rows.append(
            (
                university,
                vendor,
                product,
                f"Д-2026/{100 + index}",
                signed_at.strftime("%d.%m.%Y"),
                valid_until.strftime("%d.%m.%Y"),
                STATUSES[index % len(STATUSES)],
                manager,
                CONTACTS[index % len(CONTACTS)],
                "Заявка с сайта" if index % 3 == 0 else "",
            )
        )
    return rows


def build_workbook(base_day: date | None = None) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Взаимодействия"
    sheet.append(list(HEADERS))
    for row in _rows(base_day or date.today()):
        sheet.append(list(row))
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def main() -> None:
    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE_PATH.write_bytes(build_workbook())
    print(f"Фикстура записана в {FIXTURE_PATH.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
