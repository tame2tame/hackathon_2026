"""Демо-данные v0 (docs/PLAN.md, B-07): те же шесть связок, что во фронтенд-фикстурах.

Данные синтетические: люди, договоры и email вымышлены, домен example.com зарезервирован.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.roles import Role
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
from app.modules.interactions.models import Contract, Interaction, Transition
from app.modules.radar.service import recompute_signals
from app.modules.workflow.defaults import BASE_STAGES, ensure_default_workflow
from app.modules.workflow.models import Stage

DEMO_USERS: tuple[tuple[str, str, Role], ...] = (
    ("anna.smirnova@example.com", "Анна Смирнова", Role.KAM),
    ("mikhail.volkov@example.com", "Михаил Волков", Role.KAM),
    ("roman.kovalev@example.com", "Роман Ковалёв", Role.MANAGER),
    ("alina.denisova@example.com", "Алина Денисова", Role.ADMIN),
)

DIRECTIONS: tuple[tuple[str, str], ...] = (
    ("devops", "DevOps"),
    ("data_analysis", "Анализ данных"),
    ("mobile", "Мобильная разработка"),
    ("web", "Веб-разработка"),
    ("project_management", "Управление проектами"),
    ("ai", "Искусственный интеллект"),
    ("blockchain", "Блокчейн"),
)

# Программа → (направление, вендор, продукт)
PROGRAMS: tuple[tuple[str, str, str, str], ...] = (
    ("DevOps-инженерия", "devops", "Базис", "Базис"),
    ("Мобильная разработка", "mobile", "Открытая мобильная платформа", "ОС Аврора"),
    ("Анализ данных", "data_analysis", "Loginom", "Loginom"),
    ("Веб-разработка", "web", "Акола", "Акола"),
)

UNIVERSITIES: tuple[tuple[str, str, str, str], ...] = (
    ("МГТУ им. Н. Э. Баумана", "МГТУ", "Москва", "Москва"),
    ("Университет ИТМО", "ИТМО", "Санкт-Петербург", "Санкт-Петербург"),
    ("Уральский федеральный университет", "УрФУ", "Свердловская область", "Екатеринбург"),
    ("Казанский федеральный университет", "КФУ", "Республика Татарстан", "Казань"),
    ("Новосибирский государственный университет", "НГУ", "Новосибирская область", "Новосибирск"),
    (
        "Санкт-Петербургский политехнический университет",
        "СПбПУ",
        "Санкт-Петербург",
        "Санкт-Петербург",
    ),
)


@dataclass(frozen=True, slots=True)
class DemoInteraction:
    university: str
    program: str
    owner_email: str
    stage_code: str
    days_on_stage: int
    inactive_days: int
    contract_number: str | None = None
    license_days_left: int | None = None


# Каждая связка заложена под один сценарий радара, как во фронтенд-фикстурах.
DEMO_INTERACTIONS: tuple[DemoInteraction, ...] = (
    DemoInteraction("МГТУ", "DevOps-инженерия", "anna.smirnova@example.com", "signing", 41, 5),
    DemoInteraction(
        "ИТМО",
        "Мобильная разработка",
        "anna.smirnova@example.com",
        "classes",
        8,
        2,
        "Д-2026/042",
        19,
    ),
    DemoInteraction(
        "УрФУ",
        "Анализ данных",
        "mikhail.volkov@example.com",
        "materials_transfer",
        9,
        1,
        "Д-2026/031",
        400,
    ),
    DemoInteraction("КФУ", "Веб-разработка", "anna.smirnova@example.com", "meeting", 23, 23),
    DemoInteraction(
        "НГУ", "DevOps-инженерия", "mikhail.volkov@example.com", "documents_exchange", 18, 3
    ),
    DemoInteraction(
        "СПбПУ",
        "Мобильная разработка",
        "anna.smirnova@example.com",
        "teacher_training",
        12,
        2,
        "Д-2026/068",
        44,
    ),
)

PREVIOUS_STAGE_DAYS = 7


async def seed_demo(session: AsyncSession, now: datetime) -> bool:
    """Загружает демо-данные. Возвращает False, если они уже есть."""
    already = await session.scalar(select(Interaction.id).where(Interaction.source == "demo"))
    if already is not None:
        return False

    version = await ensure_default_workflow(session)
    stages = {
        stage.code: stage
        for stage in await session.scalars(select(Stage).where(Stage.version_id == version.id))
    }

    users = await _seed_users(session)
    programs = await _seed_catalogs(session)
    universities = {}
    for name, short_name, region, city in UNIVERSITIES:
        university = University(name=name, short_name=short_name, region=region, city=city)
        session.add(university)
        universities[short_name] = university
    await session.flush()

    ids: list[uuid.UUID] = []
    for spec in DEMO_INTERACTIONS:
        program, product = programs[spec.program]
        university = universities[spec.university]
        contract = None
        if spec.contract_number and spec.license_days_left is not None:
            valid_until = now.date() + timedelta(days=spec.license_days_left)
            contract = Contract(
                university_id=university.id,
                number=spec.contract_number,
                signed_at=valid_until - timedelta(days=365),
                license_signed_at=valid_until - timedelta(days=365),
                license_valid_until=valid_until,
                license_term_years=1,
                transfer_status="Передано",
            )
            session.add(contract)
            await session.flush()

        entered_at = now - timedelta(days=spec.days_on_stage)
        interaction = Interaction(
            university_id=university.id,
            program_id=program.id,
            product_id=product.id,
            contract_id=contract.id if contract else None,
            workflow_version_id=version.id,
            current_stage_id=stages[spec.stage_code].id,
            stage_entered_at=entered_at,
            owner_user_id=users[spec.owner_email].id,
            source="demo",
            last_activity_at=now - timedelta(days=spec.inactive_days),
        )
        session.add(interaction)
        await session.flush()
        # Дата создания совпадает с первым переходом: иначе отчёт за прошлый период
        # не увидит взаимодействие, которое тогда уже велось.
        interaction.created_at = _add_history(
            session, interaction, stages, spec.stage_code, entered_at
        )
        ids.append(interaction.id)

    await session.flush()
    await recompute_signals(session, ids, now)
    return True


async def _seed_users(session: AsyncSession) -> dict[str, AppUser]:
    users = {
        email: AppUser(email=email, full_name=name, role=role.value)
        for email, name, role in DEMO_USERS
    }
    session.add_all(users.values())
    await session.flush()
    manager = users["roman.kovalev@example.com"]
    team = Team(name="Центр и Северо-Запад", manager_user_id=manager.id)
    session.add(team)
    await session.flush()
    for email in ("anna.smirnova@example.com", "mikhail.volkov@example.com", manager.email):
        users[email].team_id = team.id
    return users


async def _seed_catalogs(session: AsyncSession) -> dict[str, tuple[Program, Product]]:
    directions = {code: Direction(code=code, name=name) for code, name in DIRECTIONS}
    session.add_all(directions.values())
    await session.flush()

    result: dict[str, tuple[Program, Product]] = {}
    for program_name, direction_code, vendor_name, product_name in PROGRAMS:
        vendor = Vendor(name=vendor_name)
        session.add(vendor)
        await session.flush()
        product = Product(vendor_id=vendor.id, name=product_name)
        program = Program(direction_id=directions[direction_code].id, name=program_name)
        session.add_all([product, program])
        await session.flush()
        session.add(ProgramProduct(program_id=program.id, product_id=product.id, is_default=True))
        await session.execute(
            product_direction.insert().values(
                product_id=product.id, direction_id=directions[direction_code].id
            )
        )
        result[program_name] = (program, product)
    return result


def _add_history(
    session: AsyncSession,
    interaction: Interaction,
    stages: dict[str, Stage],
    current_code: str,
    entered_at: datetime,
) -> datetime:
    """История от первого этапа до текущего; возвращает дату первого перехода."""
    path = [s.code for s in BASE_STAGES if s.code != "documents_revision"]
    passed = path[: path.index(current_code) + 1]
    started_at = entered_at - timedelta(days=PREVIOUS_STAGE_DAYS * (len(passed) - 1))
    previous: Stage | None = None
    for step, code in enumerate(passed):
        stage = stages[code]
        session.add(
            Transition(
                interaction_id=interaction.id,
                from_stage_id=previous.id if previous else None,
                to_stage_id=stage.id,
                occurred_at=started_at + timedelta(days=PREVIOUS_STAGE_DAYS * step),
                actor_user_id=interaction.owner_user_id,
                comment="Демо-история" if previous else "Взаимодействие создано",
                source="import",
            )
        )
        previous = stage
    return started_at
