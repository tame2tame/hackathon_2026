"""Демо-стенд v1: 96 вузов, около 350 взаимодействий, год истории и месячные показатели.

Стенд детерминирован: один и тот же `random.Random(SEED)` даёт одинаковые данные, поэтому демо
воспроизводится и на чужой машине. Шесть связок v0 остаются без изменений, а проблемы для радара
заложены ровно в перечисленном количестве — их же проверяет тест.

Запуск: `python -m scripts.seed --full`. Повторный запуск ничего не дублирует.
"""

import hashlib
import io
import random
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.roles import Role
from app.core.storage import Storage, get_storage
from app.demo import seed_demo
from app.modules.catalogs.models import (
    AppUser,
    Direction,
    Product,
    Program,
    ProgramProduct,
    Team,
    University,
    Vendor,
    product_direction,
)
from app.modules.interactions.models import Attachment, Contract, Interaction, Transition
from app.modules.metrics.models import METRIC_KINDS, ProgramMetric
from app.modules.radar.service import recompute_signals
from app.modules.workflow.defaults import BASE_STAGES, ensure_default_workflow
from app.modules.workflow.models import Stage

SEED = 2026
UNIVERSITY_TOTAL = 96
INTERACTION_TOTAL = 350
HISTORY_MONTHS = 12
KAM_TOTAL = 20

# Заложенные проблемы: ровно столько сигналов радар должен показать сверх демо-данных v0.
OVERDUE_SIGNING = 7
MISSING_DOCUMENT = 4
STALLED = 3
PLANTED = OVERDUE_SIGNING + MISSING_DOCUMENT + STALLED

PDF_BYTES = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"

CITIES = (
    "Москва",
    "Санкт-Петербург",
    "Новосибирск",
    "Екатеринбург",
    "Казань",
    "Нижний Новгород",
    "Челябинск",
    "Самара",
    "Омск",
    "Ростов-на-Дону",
    "Уфа",
    "Красноярск",
    "Воронеж",
    "Пермь",
    "Волгоград",
    "Краснодар",
    "Саратов",
    "Тюмень",
    "Тольятти",
    "Ижевск",
    "Барнаул",
    "Ульяновск",
    "Иркутск",
    "Хабаровск",
    "Ярославль",
    "Владивосток",
    "Махачкала",
    "Томск",
    "Оренбург",
    "Кемерово",
)
# Город ставится в скобках: так название не зависит от падежей и остаётся уникальным.
UNIVERSITY_KINDS = (
    ("Государственный университет", "ГУ"),
    ("Политехнический университет", "ПУ"),
    ("Технологический институт", "ТИ"),
)
REGIONS = ("Центр", "Северо-Запад", "Поволжье", "Юг", "Урал", "Сибирь", "Дальний Восток")

# Программа → (направление, вендор, продукт). Первые четыре совпадают с демо-данными v0.
PROGRAMS_V1: tuple[tuple[str, str, str, str], ...] = (
    ("DevOps-инженерия", "devops", "Базис", "Базис"),
    ("Мобильная разработка", "mobile", "Открытая мобильная платформа", "ОС Аврора"),
    ("Анализ данных", "data_analysis", "Loginom", "Loginom"),
    ("Веб-разработка", "web", "Акола", "Акола"),
    ("Контейнеризация и оркестрация", "devops", "Ред Софт", "РЕД ОС"),
    ("Инженерия данных", "data_analysis", "Postgres Professional", "Postgres Pro"),
    ("Управление ИТ-проектами", "project_management", "Новые облачные технологии", "МойОфис"),
    ("Машинное обучение", "ai", "Т1", "Сфера"),
    ("Распределённые реестры", "blockchain", "Диасофт", "Digital Q"),
    ("Промышленное проектирование", "web", "Аскон", "Компас-3D"),
)

TEAMS = ("Центр и Северо-Запад", "Поволжье и Юг", "Урал и Сибирь")
FIRST_NAMES = (
    "Алексей", "Мария", "Дмитрий", "Екатерина", "Сергей", "Ольга", "Иван", "Наталья",
    "Павел", "Ирина", "Артём", "Светлана", "Никита", "Юлия", "Максим", "Елена",
    "Андрей", "Татьяна", "Илья", "Анастасия",
)  # fmt: skip
LAST_NAMES = (
    "Соколов", "Морозова", "Лебедев", "Новикова", "Козлов", "Егорова", "Фёдоров", "Зайцева",
    "Кузьмин", "Романова", "Тарасов", "Белова", "Никитин", "Орлова", "Гусев", "Сорокина",
    "Макаров", "Крылова", "Логинов", "Дьяконова",
)  # fmt: skip

QUIET_STAGES = ("contact_search", "communication", "meeting", "documents_exchange", "classes")


@dataclass(frozen=True, slots=True)
class Plan:
    """Что именно закладывается в одно взаимодействие."""

    stage_code: str
    days_on_stage: int
    inactive_days: int
    with_contract: bool
    document: bool


def stage_norms() -> dict[str, int]:
    return {stage.code: stage.norm_days for stage in BASE_STAGES if stage.norm_days}


def university_specs(rng: random.Random) -> list[tuple[str, str, str, str]]:
    """90 вузов сверх шести из демо-данных v0: город и тип дают уникальное название."""
    specs: list[tuple[str, str, str, str]] = []
    for city in CITIES:
        for kind, suffix in UNIVERSITY_KINDS:
            specs.append(
                (f"{kind} ({city})", f"{city[:3].upper()}{suffix}", rng.choice(REGIONS), city)
            )
    return specs[: UNIVERSITY_TOTAL - 6]


def plans(rng: random.Random, count: int) -> list[Plan]:
    """План на каждое взаимодействие: сначала проблемные, затем спокойные."""
    norms = stage_norms()
    result: list[Plan] = []

    signing = norms["signing"]
    for _ in range(OVERDUE_SIGNING):
        # Затянутое подписание: больше двух норм на этапе, но договор приложен.
        result.append(Plan("signing", rng.randint(2 * signing + 3, 4 * signing), 3, True, True))

    transfer = norms["materials_transfer"]
    for _ in range(MISSING_DOCUMENT):
        # Половина нормы прошла, документа нет; до просрочки этап ещё не дошёл.
        result.append(
            Plan("materials_transfer", rng.randint(transfer // 2 + 1, transfer - 1), 4, True, False)
        )

    for _ in range(STALLED):
        # Этап с большой нормой: просрочки нет, но активности не было больше трёх недель.
        result.append(Plan("classes", rng.randint(25, 60), rng.randint(24, 40), True, False))

    while len(result) < count:
        stage_code = rng.choice(QUIET_STAGES)
        norm = norms[stage_code]
        result.append(
            Plan(
                stage_code,
                rng.randint(1, max(2, norm // 3)),
                rng.randint(0, 14),
                rng.random() < 0.6,
                False,
            )
        )
    return result


async def _catalogs(
    session: AsyncSession, rng: random.Random
) -> tuple[list[University], list[tuple[Program, Product]]]:
    directions = {
        direction.code: direction for direction in await session.scalars(select(Direction))
    }
    vendors = {vendor.name: vendor for vendor in await session.scalars(select(Vendor))}
    programs = {program.name: program for program in await session.scalars(select(Program))}
    products = {product.name: product for product in await session.scalars(select(Product))}
    linked = {
        (link.program_id, link.product_id) for link in await session.scalars(select(ProgramProduct))
    }

    pairs: list[tuple[Program, Product]] = []
    for program_name, direction_code, vendor_name, product_name in PROGRAMS_V1:
        if vendor_name not in vendors:
            vendors[vendor_name] = Vendor(name=vendor_name)
            session.add(vendors[vendor_name])
            await session.flush()
        if product_name not in products:
            products[product_name] = Product(vendor_id=vendors[vendor_name].id, name=product_name)
            session.add(products[product_name])
        if program_name not in programs:
            programs[program_name] = Program(
                direction_id=directions[direction_code].id, name=program_name
            )
            session.add(programs[program_name])
        await session.flush()

        program, product = programs[program_name], products[product_name]
        if (program.id, product.id) not in linked:
            session.add(
                ProgramProduct(program_id=program.id, product_id=product.id, is_default=True)
            )
            await session.execute(
                product_direction.insert().values(
                    product_id=product.id, direction_id=directions[direction_code].id
                )
            )
            linked.add((program.id, product.id))
        pairs.append((program, product))

    existing = list(await session.scalars(select(University)))
    fresh: list[University] = []
    for name, short_name, region, city in university_specs(rng):
        university = University(name=name, short_name=short_name, region=region, city=city)
        session.add(university)
        fresh.append(university)
    await session.flush()
    # Проблемные записи заводятся на новых вузах: там гарантированно нет прежних взаимодействий.
    return fresh + existing, pairs


async def _people(session: AsyncSession) -> list[AppUser]:
    """Три команды и двадцать КАМов сверх четырёх пользователей демо-данных v0."""
    teams = {team.name: team for team in await session.scalars(select(Team))}
    for name in TEAMS:
        if name not in teams:
            teams[name] = Team(name=name)
            session.add(teams[name])
    await session.flush()

    known = {user.email for user in await session.scalars(select(AppUser))}
    kams: list[AppUser] = []
    for index in range(KAM_TOTAL):
        email = f"kam{index + 1:02d}@example.com"
        if email in known:
            continue
        user = AppUser(
            email=email,
            full_name=f"{FIRST_NAMES[index]} {LAST_NAMES[index]}",
            role=Role.KAM.value,
            team_id=teams[TEAMS[index % len(TEAMS)]].id,
        )
        session.add(user)
        kams.append(user)
    await session.flush()
    all_kams = await session.scalars(select(AppUser).where(AppUser.role == Role.KAM.value))
    return list(all_kams)


def _history(
    session: AsyncSession,
    interaction: Interaction,
    stages: dict[str, Stage],
    stage_code: str,
    entered_at: datetime,
    actor_id: uuid.UUID,
    rng: random.Random,
) -> None:
    """Путь от первого этапа до текущего, уложенный в год до входа на текущий этап."""
    path = [stage.code for stage in BASE_STAGES if stage.code != "documents_revision"]
    passed = path[: path.index(stage_code) + 1]
    step_days = max(1, (HISTORY_MONTHS * 30) // max(1, len(passed)))
    occurred_at = entered_at - timedelta(days=step_days * (len(passed) - 1))
    previous: Stage | None = None
    for code in passed:
        stage = stages[code]
        session.add(
            Transition(
                interaction_id=interaction.id,
                from_stage_id=previous.id if previous else None,
                to_stage_id=stage.id,
                occurred_at=occurred_at,
                actor_user_id=actor_id,
                comment="Взаимодействие создано" if previous is None else "Этап пройден",
                # История стенда считается загруженной: ручной ввод помечался бы manual.
                source="import",
            )
        )
        previous = stage
        occurred_at += timedelta(days=rng.randint(max(1, step_days - 2), step_days + 2))


def _document(
    storage: Storage, interaction: Interaction, stage: Stage, uploaded_by: uuid.UUID, now: datetime
) -> Attachment:
    """Подписанный договор для затянутого этапа: иначе радар добавил бы сигнал «нет документа»."""
    attachment_id = uuid.uuid4()
    storage_key = f"interactions/{interaction.id}/{attachment_id}"
    storage.save(storage_key, io.BytesIO(PDF_BYTES))
    return Attachment(
        id=attachment_id,
        interaction_id=interaction.id,
        stage_id=stage.id,
        document_type="signed_contract",
        file_name="Договор.pdf",
        mime_type="application/pdf",
        size_bytes=len(PDF_BYTES),
        sha256=hashlib.sha256(PDF_BYTES).hexdigest(),
        storage_key=storage_key,
        uploaded_by=uploaded_by,
        uploaded_at=now,
    )


def month_starts(now: datetime) -> list[date]:
    months: list[date] = []
    year, month = now.year, now.month
    for _ in range(HISTORY_MONTHS):
        months.append(date(year, month, 1))
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return sorted(months)


def _metrics(
    session: AsyncSession,
    pairs: Sequence[tuple[uuid.UUID, uuid.UUID]],
    now: datetime,
    rng: random.Random,
) -> None:
    """Заявки, обучающиеся и потоки по месяцам: значения растут от месяца к месяцу."""
    for university_id, program_id in pairs:
        base = {"applications": rng.randint(20, 90), "students": rng.randint(15, 70), "streams": 2}
        for index, month in enumerate(month_starts(now)):
            for metric in METRIC_KINDS:
                value = int(base[metric] * (1 + index * rng.uniform(0.01, 0.06)))
                session.add(
                    ProgramMetric(
                        university_id=university_id,
                        program_id=program_id,
                        period_month=month,
                        metric=metric,
                        value=max(1, value),
                        source="demo",
                    )
                )


async def seed_full(session: AsyncSession, now: datetime) -> bool:
    """Загружает стенд v1. Возвращает False, если он уже загружен."""
    if await session.scalar(select(ProgramMetric.id).limit(1)) is not None:
        return False

    rng = random.Random(SEED)  # noqa: S311 — демо-данные, а не криптография
    await seed_demo(session, now)
    version = await ensure_default_workflow(session)
    stages = {
        stage.code: stage
        for stage in await session.scalars(select(Stage).where(Stage.version_id == version.id))
    }
    universities, pairs = await _catalogs(session, rng)
    kams = await _people(session)
    storage = get_storage()

    taken = {
        (interaction.university_id, interaction.program_id, interaction.product_id)
        for interaction in await session.scalars(select(Interaction))
    }
    created: list[uuid.UUID] = []
    metric_pairs: set[tuple[uuid.UUID, uuid.UUID]] = set()

    for index, plan in enumerate(plans(rng, INTERACTION_TOTAL)):
        # Проблемные записи получают свой вуз по порядку, чтобы их не отсеяло совпадение тройки.
        university = universities[index] if index < PLANTED else rng.choice(universities)
        program, product = pairs[index % len(pairs)] if index < PLANTED else rng.choice(pairs)
        key = (university.id, program.id, product.id)
        if key in taken:
            continue
        taken.add(key)

        owner = kams[index % len(kams)] if index < PLANTED else rng.choice(kams)
        entered_at = now - timedelta(days=plan.days_on_stage)
        contract = None
        if plan.with_contract:
            valid_until = now.date() + timedelta(days=rng.randint(120, 900))
            contract = Contract(
                university_id=university.id,
                number=f"Д-2026/{index:04d}",
                signed_at=valid_until - timedelta(days=365),
                license_signed_at=valid_until - timedelta(days=365),
                license_valid_until=valid_until,
                license_term_years=1,
                transfer_status="Передано" if plan.stage_code == "classes" else "В работе",
            )
            session.add(contract)
            await session.flush()

        interaction = Interaction(
            university_id=university.id,
            program_id=program.id,
            product_id=product.id,
            contract_id=contract.id if contract else None,
            workflow_version_id=version.id,
            current_stage_id=stages[plan.stage_code].id,
            stage_entered_at=entered_at,
            owner_user_id=owner.id,
            source="demo",
            last_activity_at=now - timedelta(days=plan.inactive_days),
        )
        session.add(interaction)
        await session.flush()
        _history(session, interaction, stages, plan.stage_code, entered_at, owner.id, rng)
        if plan.document:
            session.add(_document(storage, interaction, stages[plan.stage_code], owner.id, now))
        created.append(interaction.id)
        metric_pairs.add((university.id, program.id))

    _metrics(session, sorted(metric_pairs), now, rng)
    await session.flush()
    await recompute_signals(session, created, now)
    return True
