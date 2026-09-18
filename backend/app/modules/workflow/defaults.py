"""Процессы и группы контрагентов по умолчанию: вузы (B2B, 14 этапов из ТЗ) и частные лица (B2C)."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import pairwise

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalogs.models import CounterpartyGroup
from app.modules.workflow.models import (
    Stage,
    StageNorm,
    StageTransitionRule,
    WorkflowTemplate,
    WorkflowVersion,
)

BASE_TEMPLATE_NAME = "Базовый путь взаимодействия"
B2C_TEMPLATE_NAME = "Обучение частных лиц"

UNIVERSITIES_GROUP = "universities"
INDIVIDUALS_GROUP = "individuals"


@dataclass(frozen=True, slots=True)
class StageSpec:
    code: str
    name: str
    norm_days: int | None
    kind: str = "normal"
    bulk_allowed: bool = False
    # Этап закрывается документом: без него выйти вперёд нельзя.
    required_document_types: tuple[str, ...] = ()


# Порядок и названия совпадают с интерфейсом; нормы — стартовые, руководитель меняет их в редакторе.
BASE_STAGES: tuple[StageSpec, ...] = (
    StageSpec("contact_search", "Поиск контактов", 14, kind="start", bulk_allowed=True),
    StageSpec("communication", "Коммуникация", 21, bulk_allowed=True),
    StageSpec("meeting", "Встреча", 30, bulk_allowed=True),
    StageSpec("documents_exchange", "Обмен документами", 14, bulk_allowed=True),
    StageSpec("documents_revision", "Доработка документов", 10, bulk_allowed=True),
    StageSpec(
        "signing", "Подписание", 14, bulk_allowed=True, required_document_types=("signed_contract",)
    ),
    StageSpec(
        "materials_transfer", "Передача материалов", 14, required_document_types=("transfer_act",)
    ),
    StageSpec("implementation_support", "Поддержка внедрения", 30),
    StageSpec(
        "teacher_training",
        "Обучение преподавателей",
        30,
        required_document_types=("training_confirmation",),
    ),
    StageSpec("curriculum_update", "Обновление программы", 30),
    StageSpec("classes", "Ведение занятий", 120),
    StageSpec("docs_update", "Обновление документации", 30),
    StageSpec("teacher_upskilling", "Повышение квалификации", 60),
    StageSpec("stage_control", "Контроль этапов", None, kind="final"),
)

# Обучение частных и юридических лиц: короче вузовского пути и держится на оплате и аттестации.
B2C_STAGES: tuple[StageSpec, ...] = (
    StageSpec("application", "Заявка", 3, kind="start", bulk_allowed=True),
    StageSpec("consultation", "Консультация", 7, bulk_allowed=True),
    StageSpec("offer", "Договор-оферта", 7, required_document_types=("signed_offer",)),
    StageSpec("payment", "Оплата", 10, required_document_types=("payment_confirmation",)),
    StageSpec("enrollment", "Зачисление в LMS", 3, bulk_allowed=True),
    StageSpec("training", "Обучение", 90),
    StageSpec("certification", "Итоговая аттестация", 14, required_document_types=("certificate",)),
    StageSpec("completed", "Завершено", None, kind="final"),
)


@dataclass(frozen=True, slots=True)
class GroupSpec:
    code: str
    name: str
    description: str
    position: int


UNIVERSITIES = GroupSpec(
    UNIVERSITIES_GROUP, "Вузы (B2B)", "Работа с вузами по ИТ-программам и продуктам", 1
)
INDIVIDUALS = GroupSpec(
    INDIVIDUALS_GROUP,
    "Частные лица (B2C)",
    "Обучение физических и юридических лиц по программам ИТ Школы",
    2,
)


def base_transition_pairs() -> list[tuple[str, str]]:
    """Переходы на следующий этап; с «Обмена документами» можно сразу на «Подписание»."""
    codes = [stage.code for stage in BASE_STAGES]
    pairs = list(pairwise(codes))
    pairs.append(("documents_exchange", "signing"))
    return pairs


def b2c_transition_pairs() -> list[tuple[str, str]]:
    return list(pairwise(stage.code for stage in B2C_STAGES))


def return_pairs(forward: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Возврат на шаг назад для каждого перехода вперёд.

    Процесс бюрократический: что-то забыли — вернулись. Возврат требует объяснения, но не документа.
    """
    return [(to_code, from_code) for from_code, to_code in forward]


async def _published(session: AsyncSession, template_id: uuid.UUID) -> WorkflowVersion | None:
    version: WorkflowVersion | None = await session.scalar(
        select(WorkflowVersion)
        .where(WorkflowVersion.template_id == template_id, WorkflowVersion.status == "published")
        .order_by(WorkflowVersion.version_no.desc())
        .limit(1)
    )
    return version


async def _create_process(
    session: AsyncSession,
    name: str,
    stages: tuple[StageSpec, ...],
    forward: list[tuple[str, str]],
    *,
    is_default: bool = False,
) -> WorkflowVersion:
    """Шаблон с опубликованной первой версией: этапы, нормы, переходы вперёд и назад."""
    template = WorkflowTemplate(name=name, is_default=is_default)
    session.add(template)
    await session.flush()
    version = WorkflowVersion(
        template_id=template.id, version_no=1, status="published", published_at=datetime.now(UTC)
    )
    session.add(version)
    await session.flush()

    by_code: dict[str, Stage] = {}
    specs = {spec.code: spec for spec in stages}
    for position, spec in enumerate(stages, start=1):
        stage = Stage(
            version_id=version.id,
            code=spec.code,
            name=spec.name,
            position=position,
            kind=spec.kind,
            bulk_allowed=spec.bulk_allowed,
            required_document_types=list(spec.required_document_types),
        )
        by_code[spec.code] = stage
        session.add(stage)
        if spec.norm_days is not None:
            session.add(
                StageNorm(template_id=template.id, stage_code=spec.code, norm_days=spec.norm_days)
            )
    await session.flush()

    for from_code, to_code in forward:
        session.add(
            StageTransitionRule(
                version_id=version.id,
                from_stage_id=by_code[from_code].id,
                to_stage_id=by_code[to_code].id,
                requires_attachment=bool(specs[from_code].required_document_types),
            )
        )
    for from_code, to_code in return_pairs(forward):
        session.add(
            StageTransitionRule(
                version_id=version.id,
                from_stage_id=by_code[from_code].id,
                to_stage_id=by_code[to_code].id,
                requires_comment=True,
                requires_attachment=False,
            )
        )
    await session.flush()
    return version


async def ensure_default_workflow(session: AsyncSession) -> WorkflowVersion:
    """Базовый процесс работы с вузами с опубликованной версией 1. Идемпотентна."""
    existing = await session.scalar(
        select(WorkflowVersion)
        .join(WorkflowTemplate, WorkflowTemplate.id == WorkflowVersion.template_id)
        .where(WorkflowTemplate.is_default.is_(True), WorkflowVersion.status == "published")
        .order_by(WorkflowVersion.version_no.desc())
        .limit(1)
    )
    if existing is not None:
        return existing
    return await _create_process(
        session, BASE_TEMPLATE_NAME, BASE_STAGES, base_transition_pairs(), is_default=True
    )


async def _b2c_process(session: AsyncSession) -> WorkflowVersion:
    template = await session.scalar(
        select(WorkflowTemplate).where(WorkflowTemplate.name == B2C_TEMPLATE_NAME)
    )
    if template is not None:
        version = await _published(session, template.id)
        if version is not None:
            return version
    return await _create_process(session, B2C_TEMPLATE_NAME, B2C_STAGES, b2c_transition_pairs())


async def ensure_groups(session: AsyncSession) -> dict[str, CounterpartyGroup]:
    """Группы «Вузы (B2B)» и «Частные лица (B2C)» со своими процессами. Идемпотентна."""
    groups = {group.code: group for group in await session.scalars(select(CounterpartyGroup))}
    for spec in (UNIVERSITIES, INDIVIDUALS):
        if spec.code in groups:
            continue
        version = (
            await ensure_default_workflow(session)
            if spec.code == UNIVERSITIES_GROUP
            else await _b2c_process(session)
        )
        group = CounterpartyGroup(
            code=spec.code,
            name=spec.name,
            description=spec.description,
            workflow_template_id=version.template_id,
            position=spec.position,
        )
        session.add(group)
        groups[spec.code] = group
    await session.flush()
    return groups


async def universities_group(session: AsyncSession) -> CounterpartyGroup:
    """Группа вузов: импорт выгрузок и заявки с сайта относятся к ней."""
    return (await ensure_groups(session))[UNIVERSITIES_GROUP]
