"""Чтение workflow: версия шаблона, этапы с нормами, разрешённые переходы."""

import uuid
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import AppError, ErrorCode, FieldError
from app.core.security import CurrentUser
from app.modules.audit.models import AuditLog
from app.modules.catalogs.models import CounterpartyGroup
from app.modules.catalogs.schemas import GroupRef
from app.modules.interactions.models import Transition
from app.modules.radar.norms import suggest_norm
from app.modules.workflow.models import (
    Stage,
    StageNorm,
    StageTransitionRule,
    WorkflowTemplate,
    WorkflowVersion,
)
from app.modules.workflow.schemas import (
    AllowedTransitionOut,
    StageNormOut,
    StageOut,
    StageRef,
    TransitionRuleOut,
    WorkflowOut,
    WorkflowSummaryOut,
)


@dataclass(frozen=True, slots=True)
class GroupProcess:
    version: WorkflowVersion
    stages: dict[str, Stage]
    start: Stage


async def published_version(
    session: AsyncSession, template_id: uuid.UUID
) -> WorkflowVersion | None:
    version: WorkflowVersion | None = await session.scalar(
        select(WorkflowVersion)
        .where(WorkflowVersion.template_id == template_id, WorkflowVersion.status == "published")
        .order_by(WorkflowVersion.version_no.desc())
        .limit(1)
    )
    return version


async def group_process(session: AsyncSession, group: CounterpartyGroup) -> GroupProcess:
    """Действующая схема процесса группы, её этапы по коду и первый этап."""
    version = await published_version(session, group.workflow_template_id)
    stages = (
        {
            stage.code: stage
            for stage in await session.scalars(select(Stage).where(Stage.version_id == version.id))
        }
        if version is not None
        else {}
    )
    if version is None or not stages:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            f"У группы «{group.name}» нет опубликованного процесса.",
            errors=[FieldError(field="group_id", message="Нет процесса")],
        )
    start = min(stages.values(), key=lambda stage: (stage.kind != "start", stage.position))
    return GroupProcess(version, stages, start)


async def norms_by_stage_code(session: AsyncSession, template_id: uuid.UUID) -> dict[str, int]:
    rows = await session.execute(
        select(StageNorm.stage_code, StageNorm.norm_days).where(
            StageNorm.template_id == template_id
        )
    )
    return {code: days for code, days in rows.tuples()}


async def _version_of(session: AsyncSession, template_id: uuid.UUID | None) -> WorkflowVersion:
    """Действующая схема шаблона; без шаблона — базового процесса работы с вузами."""
    stmt = (
        select(WorkflowVersion)
        .join(WorkflowTemplate, WorkflowTemplate.id == WorkflowVersion.template_id)
        .where(WorkflowVersion.status == "published")
        .order_by(WorkflowVersion.version_no.desc())
        .options(selectinload(WorkflowVersion.stages), selectinload(WorkflowVersion.template))
        .limit(1)
    )
    if template_id is None:
        stmt = stmt.where(WorkflowTemplate.is_default.is_(True))
    else:
        stmt = stmt.where(WorkflowTemplate.id == template_id)
    version = await session.scalar(stmt)
    if version is None:
        detail = (
            "Базовый workflow не создан: выполните make seed."
            if template_id is None
            else "Процесс не найден или ещё не опубликован."
        )
        raise AppError(ErrorCode.NOT_FOUND, detail)
    return version


async def get_workflow(session: AsyncSession, template_id: uuid.UUID | None = None) -> WorkflowOut:
    version = await _version_of(session, template_id)
    norms = await norms_by_stage_code(session, version.template_id)
    rules = await session.scalars(
        select(StageTransitionRule).where(StageTransitionRule.version_id == version.id)
    )
    return WorkflowOut(
        id=version.id,
        template_id=version.template_id,
        name=version.template.name,
        version_no=version.version_no,
        stages=[
            StageOut(
                id=stage.id,
                code=stage.code,
                name=stage.name,
                position=stage.position,
                kind=stage.kind,
                bulk_allowed=stage.bulk_allowed,
                required_document_types=list(stage.required_document_types),
                norm_days=norms.get(stage.code),
            )
            for stage in version.stages
        ],
        transitions=[
            TransitionRuleOut(
                from_stage_id=rule.from_stage_id,
                to_stage_id=rule.to_stage_id,
                requires_comment=rule.requires_comment,
                requires_attachment=rule.requires_attachment,
            )
            for rule in rules
        ],
    )


async def list_workflows(session: AsyncSession) -> list[WorkflowSummaryOut]:
    """Шаблоны процессов с действующей схемой, черновиком и группами, которые по ним работают."""
    templates = list(
        await session.scalars(
            select(WorkflowTemplate)
            .where(WorkflowTemplate.archived_at.is_(None))
            .order_by(WorkflowTemplate.is_default.desc(), WorkflowTemplate.name)
        )
    )
    versions = list(
        await session.scalars(
            select(WorkflowVersion)
            .where(WorkflowVersion.status.in_(("published", "draft")))
            .order_by(WorkflowVersion.version_no)
        )
    )
    published = {v.template_id: v for v in versions if v.status == "published"}
    drafts = {v.template_id: v for v in versions if v.status == "draft"}
    groups: dict[uuid.UUID, list[GroupRef]] = defaultdict(list)
    for group in await session.scalars(
        select(CounterpartyGroup)
        .where(CounterpartyGroup.archived_at.is_(None))
        .order_by(CounterpartyGroup.position, CounterpartyGroup.name)
    ):
        groups[group.workflow_template_id].append(GroupRef.model_validate(group))
    return [
        WorkflowSummaryOut(
            id=template.id,
            name=template.name,
            is_default=template.is_default,
            published_version_id=published[template.id].id if template.id in published else None,
            version_no=published[template.id].version_no if template.id in published else None,
            draft_version_id=drafts[template.id].id if template.id in drafts else None,
            groups=groups[template.id],
        )
        for template in templates
    ]


async def allowed_transitions(
    session: AsyncSession, from_stage_id: uuid.UUID
) -> list[AllowedTransitionOut]:
    rules = await session.scalars(
        select(StageTransitionRule)
        .join(Stage, Stage.id == StageTransitionRule.to_stage_id)
        .where(StageTransitionRule.from_stage_id == from_stage_id)
        .options(selectinload(StageTransitionRule.to_stage))
        .order_by(Stage.position)
    )
    return [
        AllowedTransitionOut(
            to_stage=StageRef.model_validate(rule.to_stage),
            requires_comment=rule.requires_comment,
            requires_attachment=rule.requires_attachment,
        )
        for rule in rules
    ]


async def get_transition_rule(
    session: AsyncSession, from_stage_id: uuid.UUID, to_stage_id: uuid.UUID
) -> StageTransitionRule | None:
    rule: StageTransitionRule | None = await session.scalar(
        select(StageTransitionRule).where(
            StageTransitionRule.from_stage_id == from_stage_id,
            StageTransitionRule.to_stage_id == to_stage_id,
        )
    )
    return rule


async def _norm(
    session: AsyncSession, stage_code: str, template_id: uuid.UUID | None
) -> tuple[StageNorm, Stage]:
    version = await _version_of(session, template_id)
    stage = await session.scalar(
        select(Stage).where(Stage.version_id == version.id, Stage.code == stage_code)
    )
    norm = await session.scalar(
        select(StageNorm).where(
            StageNorm.template_id == version.template_id, StageNorm.stage_code == stage_code
        )
    )
    if stage is None or norm is None:
        raise AppError(ErrorCode.NOT_FOUND, "Этап не найден или у него нет нормы.")
    return norm, stage


def _norm_out(norm: StageNorm, stage: Stage) -> StageNormOut:
    return StageNormOut(
        stage_code=norm.stage_code,
        stage_name=stage.name,
        norm_days=norm.norm_days,
        source=norm.source,
        suggested_median_days=norm.suggested_median_days,
        suggested_percentile_days=norm.suggested_percentile_days,
        sample_size=norm.sample_size,
    )


async def list_norms(
    session: AsyncSession, template_id: uuid.UUID | None = None
) -> list[StageNormOut]:
    version = await _version_of(session, template_id)
    rows = await session.execute(
        select(StageNorm, Stage)
        .join(
            Stage,
            and_(Stage.version_id == version.id, Stage.code == StageNorm.stage_code),
        )
        .where(StageNorm.template_id == version.template_id)
        .order_by(Stage.position)
    )
    return [_norm_out(norm, stage) for norm, stage in rows.tuples()]


async def set_norm(
    session: AsyncSession,
    user: CurrentUser,
    stage_code: str,
    norm_days: int,
    trace_id: str | None = None,
    template_id: uuid.UUID | None = None,
) -> StageNormOut:
    norm, stage = await _norm(session, stage_code, template_id)
    before = {"norm_days": norm.norm_days, "source": norm.source}
    norm.norm_days = norm_days
    norm.source = "manual"
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="workflow.norm_changed",
            entity_kind="stage_norm",
            entity_id=norm.id,
            before=before,
            after={"norm_days": norm_days, "source": "manual"},
            trace_id=trace_id,
        )
    )
    await session.commit()
    return _norm_out(norm, stage)


async def refresh_suggestions(session: AsyncSession) -> int:
    """Считает подсказки норм по завершённым этапам всех процессов. Возвращает число обновлённых."""
    updated = 0
    for version in await session.scalars(
        select(WorkflowVersion).where(WorkflowVersion.status == "published")
    ):
        updated += await _refresh_template(session, version)
    await session.flush()
    return updated


async def _refresh_template(session: AsyncSession, version: WorkflowVersion) -> int:
    # Длительность этапа — промежуток между переходом на него и следующим переходом.
    # Этапы сопоставляются по коду: нормы шаблона переживают смену схемы.
    next_at = func.lead(Transition.occurred_at).over(
        partition_by=Transition.interaction_id, order_by=Transition.occurred_at
    )
    template_versions = select(WorkflowVersion.id).where(
        WorkflowVersion.template_id == version.template_id
    )
    rows = await session.execute(
        select(Stage.code, Transition.occurred_at, next_at.label("next_at"))
        .join(Stage, Stage.id == Transition.to_stage_id)
        .where(Stage.version_id.in_(template_versions))
    )
    durations: dict[str, list[int]] = defaultdict(list)
    for code, occurred_at, next_occurred in rows.tuples():
        if next_occurred is not None:
            durations[code].append((next_occurred - occurred_at).days)

    norms = await session.scalars(
        select(StageNorm).where(StageNorm.template_id == version.template_id)
    )
    updated = 0
    for norm in norms:
        suggestion = suggest_norm(durations.get(norm.stage_code, []))
        if suggestion is None:
            continue
        norm.suggested_median_days = suggestion.median_days
        norm.suggested_percentile_days = suggestion.percentile_days
        norm.sample_size = suggestion.sample_size
        updated += 1
    return updated


async def accept_suggestion(
    session: AsyncSession,
    user: CurrentUser,
    stage_code: str,
    trace_id: str | None = None,
    template_id: uuid.UUID | None = None,
) -> StageNormOut:
    """Принять подсказку: нормой становится 80-й перцентиль, в который укладывается большинство."""
    norm, stage = await _norm(session, stage_code, template_id)
    if norm.suggested_percentile_days is None:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Для этого этапа ещё нет подсказки: нужно не меньше пяти завершённых этапов.",
        )
    before = {"norm_days": norm.norm_days, "source": norm.source}
    norm.norm_days = norm.suggested_percentile_days
    norm.source = "suggested"
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="workflow.norm_suggestion_accepted",
            entity_kind="stage_norm",
            entity_id=norm.id,
            before=before,
            after={"norm_days": norm.norm_days, "source": "suggested"},
            trace_id=trace_id,
        )
    )
    await session.commit()
    return _norm_out(norm, stage)
