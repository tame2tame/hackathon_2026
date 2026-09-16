"""Редактор процесса: черновик версии, правка этапов и публикация с переносом записей.

Опубликованная версия неизменна по структуре — на неё ссылаются взаимодействия. Менять можно
только черновик; при публикации открытые записи переезжают на новую версию переходом
`source=migration`, а норма следует за кодом этапа, поэтому переименование её не теряет.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ErrorCode, FieldError
from app.core.security import CurrentUser
from app.modules.audit.models import AuditLog
from app.modules.interactions.models import Interaction, Transition
from app.modules.workflow.models import (
    Stage,
    StageNorm,
    StageTransitionRule,
    WorkflowTemplate,
    WorkflowVersion,
)
from app.modules.workflow.schemas import (
    PublishRequest,
    StageOut,
    TransitionRuleOut,
    VersionOut,
    VersionPatch,
)

OPEN_STATUSES = ("active", "paused")


async def _version(session: AsyncSession, version_id: uuid.UUID) -> WorkflowVersion:
    version = await session.get(WorkflowVersion, version_id)
    if version is None:
        raise AppError(ErrorCode.NOT_FOUND, "Версия процесса не найдена.")
    return version


async def _draft(session: AsyncSession, version_id: uuid.UUID) -> WorkflowVersion:
    version = await _version(session, version_id)
    if version.status != "draft":
        raise AppError(
            ErrorCode.WF_VERSION_NOT_DRAFT,
            "Опубликованную версию менять нельзя: создайте черновик или переименуйте этап.",
        )
    return version


async def version_out(session: AsyncSession, version: WorkflowVersion) -> VersionOut:
    stages = list(
        await session.scalars(
            select(Stage).where(Stage.version_id == version.id).order_by(Stage.position)
        )
    )
    norms = {
        code: days
        for code, days in (
            await session.execute(
                select(StageNorm.stage_code, StageNorm.norm_days).where(
                    StageNorm.template_id == version.template_id
                )
            )
        ).tuples()
    }
    rules = await session.scalars(
        select(StageTransitionRule).where(StageTransitionRule.version_id == version.id)
    )
    return VersionOut(
        id=version.id,
        template_id=version.template_id,
        version_no=version.version_no,
        status=version.status,
        published_at=version.published_at,
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
            for stage in stages
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


async def create_template(
    session: AsyncSession, user: CurrentUser, name: str, trace_id: str | None = None
) -> WorkflowTemplate:
    if await session.scalar(select(WorkflowTemplate).where(WorkflowTemplate.name == name)):
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Шаблон с таким названием уже есть.",
            errors=[FieldError(field="name", message="Название занято")],
        )
    template = WorkflowTemplate(name=name)
    session.add(template)
    await session.flush()
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="workflow.template_created",
            entity_kind="workflow_template",
            entity_id=template.id,
            after={"name": name},
            trace_id=trace_id,
        )
    )
    await session.commit()
    return template


async def create_draft(
    session: AsyncSession, user: CurrentUser, template_id: uuid.UUID, trace_id: str | None = None
) -> WorkflowVersion:
    """Черновик — копия последней версии шаблона: править легче, чем собирать заново."""
    template = await session.get(WorkflowTemplate, template_id)
    if template is None:
        raise AppError(ErrorCode.NOT_FOUND, "Шаблон процесса не найден.")

    latest = await session.scalar(
        select(WorkflowVersion)
        .where(WorkflowVersion.template_id == template_id)
        .order_by(WorkflowVersion.version_no.desc())
        .limit(1)
    )
    next_no = (latest.version_no + 1) if latest else 1
    draft = WorkflowVersion(template_id=template_id, version_no=next_no, status="draft")
    session.add(draft)
    await session.flush()

    if latest is not None:
        source_stages = list(
            await session.scalars(
                select(Stage).where(Stage.version_id == latest.id).order_by(Stage.position)
            )
        )
        copies = {
            stage.code: Stage(
                version_id=draft.id,
                code=stage.code,
                name=stage.name,
                position=stage.position,
                kind=stage.kind,
                bulk_allowed=stage.bulk_allowed,
                required_document_types=list(stage.required_document_types),
            )
            for stage in source_stages
        }
        session.add_all(copies.values())
        await session.flush()
        by_id = {stage.id: stage.code for stage in source_stages}
        rules = await session.scalars(
            select(StageTransitionRule).where(StageTransitionRule.version_id == latest.id)
        )
        for rule in rules:
            session.add(
                StageTransitionRule(
                    version_id=draft.id,
                    from_stage_id=copies[by_id[rule.from_stage_id]].id,
                    to_stage_id=copies[by_id[rule.to_stage_id]].id,
                    requires_comment=rule.requires_comment,
                    requires_attachment=rule.requires_attachment,
                )
            )
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="workflow.draft_created",
            entity_kind="workflow_version",
            entity_id=draft.id,
            after={"template_id": str(template_id), "version_no": next_no},
            trace_id=trace_id,
        )
    )
    await session.commit()
    return draft


async def patch_version(
    session: AsyncSession,
    user: CurrentUser,
    version_id: uuid.UUID,
    payload: VersionPatch,
    trace_id: str | None = None,
) -> WorkflowVersion:
    draft = await _draft(session, version_id)

    if payload.stages is not None:
        codes = [stage.code for stage in payload.stages]
        if len(set(codes)) != len(codes):
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Коды этапов повторяются.",
                errors=[FieldError(field="stages", message="Код этапа должен быть уникален")],
            )
        existing = list(await session.scalars(select(Stage).where(Stage.version_id == draft.id)))
        for rule in await session.scalars(
            select(StageTransitionRule).where(StageTransitionRule.version_id == draft.id)
        ):
            await session.delete(rule)
        for stage in existing:
            await session.delete(stage)
        await session.flush()

        for stage_draft in payload.stages:
            session.add(
                Stage(
                    version_id=draft.id,
                    code=stage_draft.code,
                    name=stage_draft.name,
                    position=stage_draft.position,
                    kind=stage_draft.kind,
                    bulk_allowed=stage_draft.bulk_allowed,
                    required_document_types=list(stage_draft.required_document_types),
                )
            )
            if stage_draft.norm_days is not None:
                await _set_norm(session, draft.template_id, stage_draft.code, stage_draft.norm_days)
        await session.flush()

    if payload.transitions is not None:
        stages = {
            stage.code: stage
            for stage in await session.scalars(select(Stage).where(Stage.version_id == draft.id))
        }
        unknown = sorted(
            {
                code
                for rule in payload.transitions
                for code in (rule.from_code, rule.to_code)
                if code not in stages
            }
        )
        if unknown:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                f"В версии нет этапов: {', '.join(unknown)}.",
                errors=[FieldError(field="transitions", message="Неизвестный код этапа")],
            )
        for rule in await session.scalars(
            select(StageTransitionRule).where(StageTransitionRule.version_id == draft.id)
        ):
            await session.delete(rule)
        await session.flush()
        for rule_draft in payload.transitions:
            session.add(
                StageTransitionRule(
                    version_id=draft.id,
                    from_stage_id=stages[rule_draft.from_code].id,
                    to_stage_id=stages[rule_draft.to_code].id,
                    requires_comment=rule_draft.requires_comment,
                    requires_attachment=rule_draft.requires_attachment,
                )
            )

    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="workflow.draft_changed",
            entity_kind="workflow_version",
            entity_id=draft.id,
            after={
                "stages": len(payload.stages) if payload.stages is not None else None,
                "transitions": len(payload.transitions)
                if payload.transitions is not None
                else None,
            },
            trace_id=trace_id,
        )
    )
    await session.commit()
    return draft


async def _set_norm(
    session: AsyncSession, template_id: uuid.UUID, stage_code: str, norm_days: int
) -> None:
    norm = await session.scalar(
        select(StageNorm).where(
            StageNorm.template_id == template_id, StageNorm.stage_code == stage_code
        )
    )
    if norm is None:
        session.add(StageNorm(template_id=template_id, stage_code=stage_code, norm_days=norm_days))
    else:
        norm.norm_days = norm_days


async def rename_stage(
    session: AsyncSession,
    user: CurrentUser,
    stage_id: uuid.UUID,
    name: str,
    trace_id: str | None = None,
) -> Stage:
    """Переименование разрешено и в опубликованной версии: меняется подпись, а не процесс."""
    stage = await session.get(Stage, stage_id)
    if stage is None:
        raise AppError(ErrorCode.NOT_FOUND, "Этап не найден.")
    before = stage.name
    stage.name = name
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="workflow.stage_renamed",
            entity_kind="stage",
            entity_id=stage.id,
            before={"name": before},
            after={"name": name},
            trace_id=trace_id,
        )
    )
    await session.commit()
    return stage


async def publish_version(
    session: AsyncSession,
    user: CurrentUser,
    version_id: uuid.UUID,
    payload: PublishRequest,
    trace_id: str | None = None,
    now: datetime | None = None,
) -> WorkflowVersion:
    """Публикует черновик и переводит на него открытые взаимодействия прежней версии."""
    now = now or datetime.now(UTC)
    draft = await _draft(session, version_id)
    new_stages = {
        stage.code: stage
        for stage in await session.scalars(select(Stage).where(Stage.version_id == draft.id))
    }
    if not new_stages:
        raise AppError(ErrorCode.VALIDATION_ERROR, "В версии нет этапов.")

    previous = await session.scalar(
        select(WorkflowVersion)
        .where(
            WorkflowVersion.template_id == draft.template_id,
            WorkflowVersion.status == "published",
        )
        .order_by(WorkflowVersion.version_no.desc())
        .limit(1)
    )

    moved = 0
    if previous is not None:
        busy = (
            (
                await session.execute(
                    select(Stage.code, func.count(Interaction.id))
                    .select_from(Stage)
                    .join(Interaction, Interaction.current_stage_id == Stage.id)
                    .where(
                        Stage.version_id == previous.id,
                        Interaction.status.in_(OPEN_STATUSES),
                    )
                    .group_by(Stage.code)
                )
            )
            .tuples()
            .all()
        )
        # Каждый занятый этап должен куда-то переехать, иначе запись повиснет в никуда.
        missing = sorted(
            code for code, _ in busy if payload.migration_map.get(code, code) not in new_stages
        )
        if missing:
            raise AppError(
                ErrorCode.WF_MIGRATION_MAP_INCOMPLETE,
                f"Не указано, куда переносить этапы: {', '.join(missing)}.",
                errors=[
                    FieldError(field=f"migration_map.{code}", message="Нужен этап новой версии")
                    for code in missing
                ],
            )
        moved = await _move_interactions(session, user, previous, draft, new_stages, payload, now)
        previous.status = "retired"

    draft.status = "published"
    draft.published_at = now
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="workflow.version_published",
            entity_kind="workflow_version",
            entity_id=draft.id,
            before={"previous_version_id": str(previous.id) if previous else None},
            after={"version_no": draft.version_no, "moved_interactions": moved},
            trace_id=trace_id,
        )
    )
    await session.commit()
    return draft


async def _move_interactions(
    session: AsyncSession,
    user: CurrentUser,
    previous: WorkflowVersion,
    draft: WorkflowVersion,
    new_stages: dict[str, Stage],
    payload: PublishRequest,
    now: datetime,
) -> int:
    old_codes = {
        stage.id: stage.code
        for stage in await session.scalars(select(Stage).where(Stage.version_id == previous.id))
    }
    interactions = list(
        await session.scalars(
            select(Interaction).where(
                Interaction.workflow_version_id == previous.id,
                Interaction.status.in_(OPEN_STATUSES),
            )
        )
    )
    for interaction in interactions:
        old_code = old_codes[interaction.current_stage_id]
        target = new_stages[payload.migration_map.get(old_code, old_code)]
        session.add(
            Transition(
                interaction_id=interaction.id,
                from_stage_id=interaction.current_stage_id,
                to_stage_id=target.id,
                occurred_at=now,
                actor_user_id=user.id,
                comment=f"Перенос на версию {draft.version_no}",
                source="migration",
            )
        )
        interaction.current_stage_id = target.id
        interaction.workflow_version_id = draft.id
        # Дата входа на этап не сбрасывается: перенос версии — не работа по взаимодействию.
        interaction.version += 1
    await session.flush()
    return len(interactions)
