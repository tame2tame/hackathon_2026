"""Базовый workflow из ТЗ: 14 этапов, нормы длительности и правила переходов."""

from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import pairwise

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.workflow.models import (
    Stage,
    StageNorm,
    StageTransitionRule,
    WorkflowTemplate,
    WorkflowVersion,
)

BASE_TEMPLATE_NAME = "Базовый путь взаимодействия"

# Эти этапы закрываются документом: договором, актом передачи, подтверждением обучения.
DOCUMENT_REQUIRED_EXITS = frozenset({"signing", "materials_transfer", "teacher_training"})


@dataclass(frozen=True, slots=True)
class StageSpec:
    code: str
    name: str
    norm_days: int | None
    kind: str = "normal"
    bulk_allowed: bool = False
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


def base_transition_pairs() -> list[tuple[str, str]]:
    """Переходы на следующий этап; с «Обмена документами» можно сразу на «Подписание»."""
    codes = [stage.code for stage in BASE_STAGES]
    pairs = list(pairwise(codes))
    pairs.append(("documents_exchange", "signing"))
    return pairs


def return_pairs(forward: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Возврат на шаг назад для каждого перехода вперёд.

    Процесс бюрократический: что-то забыли — вернулись. Возврат требует объяснения, но не документа.
    """
    return [(to_code, from_code) for from_code, to_code in forward]


async def ensure_default_workflow(session: AsyncSession) -> WorkflowVersion:
    """Создаёт базовый шаблон с опубликованной версией 1, если его ещё нет. Идемпотентна."""
    existing = await session.scalar(
        select(WorkflowVersion)
        .join(WorkflowTemplate, WorkflowTemplate.id == WorkflowVersion.template_id)
        .where(WorkflowTemplate.is_default.is_(True), WorkflowVersion.status == "published")
        .order_by(WorkflowVersion.version_no.desc())
        .limit(1)
    )
    if existing is not None:
        return existing

    template = WorkflowTemplate(name=BASE_TEMPLATE_NAME, is_default=True)
    session.add(template)
    await session.flush()
    version = WorkflowVersion(
        template_id=template.id, version_no=1, status="published", published_at=datetime.now(UTC)
    )
    session.add(version)
    await session.flush()

    stages: dict[str, Stage] = {}
    for position, spec in enumerate(BASE_STAGES, start=1):
        stage = Stage(
            version_id=version.id,
            code=spec.code,
            name=spec.name,
            position=position,
            kind=spec.kind,
            bulk_allowed=spec.bulk_allowed,
            required_document_types=list(spec.required_document_types),
        )
        stages[spec.code] = stage
        session.add(stage)
        if spec.norm_days is not None:
            session.add(
                StageNorm(template_id=template.id, stage_code=spec.code, norm_days=spec.norm_days)
            )
    await session.flush()

    forward = base_transition_pairs()
    for from_code, to_code in forward:
        session.add(
            StageTransitionRule(
                version_id=version.id,
                from_stage_id=stages[from_code].id,
                to_stage_id=stages[to_code].id,
                requires_attachment=from_code in DOCUMENT_REQUIRED_EXITS,
            )
        )
    for from_code, to_code in return_pairs(forward):
        session.add(
            StageTransitionRule(
                version_id=version.id,
                from_stage_id=stages[from_code].id,
                to_stage_id=stages[to_code].id,
                requires_comment=True,
                requires_attachment=False,
            )
        )
    await session.flush()
    return version
