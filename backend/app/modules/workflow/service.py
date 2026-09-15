"""Чтение workflow: версия шаблона, этапы с нормами, разрешённые переходы."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import AppError, ErrorCode
from app.modules.workflow.models import (
    Stage,
    StageNorm,
    StageTransitionRule,
    WorkflowTemplate,
    WorkflowVersion,
)
from app.modules.workflow.schemas import (
    AllowedTransitionOut,
    StageOut,
    StageRef,
    TransitionRuleOut,
    WorkflowOut,
)


async def norms_by_stage_code(session: AsyncSession, template_id: uuid.UUID) -> dict[str, int]:
    rows = await session.execute(
        select(StageNorm.stage_code, StageNorm.norm_days).where(
            StageNorm.template_id == template_id
        )
    )
    return {code: days for code, days in rows.tuples()}


async def get_default_workflow(session: AsyncSession) -> WorkflowOut:
    version = await session.scalar(
        select(WorkflowVersion)
        .join(WorkflowTemplate, WorkflowTemplate.id == WorkflowVersion.template_id)
        .where(WorkflowTemplate.is_default.is_(True), WorkflowVersion.status == "published")
        .order_by(WorkflowVersion.version_no.desc())
        .options(selectinload(WorkflowVersion.stages), selectinload(WorkflowVersion.template))
        .limit(1)
    )
    if version is None:
        raise AppError(ErrorCode.NOT_FOUND, "Базовый workflow не создан: выполните make seed.")
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
