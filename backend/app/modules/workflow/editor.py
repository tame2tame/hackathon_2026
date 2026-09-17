"""Редактор процесса: черновик изменений, правка этапов и публикация с переносом записей.

Процесс у группы один. Черновик — это изменения до применения, а не параллельная схема:
при публикации все открытые записи переезжают на новую схему переходом `source=migration`,
а норма следует за кодом этапа, поэтому переименование её не теряет. Записи с удалённого
этапа переходят на соседний, так что изменение процесса не останавливает текущую работу.
"""

import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ErrorCode, FieldError
from app.core.roles import Role
from app.core.security import CurrentUser
from app.modules.audit.models import AuditLog
from app.modules.integrations.outbox import mark_changed
from app.modules.interactions.models import Interaction, Transition
from app.modules.notifications.service import notify
from app.modules.radar.service import recompute_signals
from app.modules.workflow.models import (
    Stage,
    StageNorm,
    StageTransitionRule,
    WorkflowTemplate,
    WorkflowVersion,
)
from app.modules.workflow.schemas import (
    PublishPreview,
    PublishRequest,
    StageDraft,
    StageMoveOut,
    StageOut,
    StageRef,
    StageRenameOut,
    TransitionDraft,
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
        await _replace_stages(session, draft, payload.stages)
    if payload.transitions is not None:
        await _replace_transitions(session, draft, payload.transitions)

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


async def _drop_transitions(session: AsyncSession, version_id: uuid.UUID) -> None:
    for rule in await session.scalars(
        select(StageTransitionRule).where(StageTransitionRule.version_id == version_id)
    ):
        await session.delete(rule)
    await session.flush()


async def _replace_stages(
    session: AsyncSession, draft: WorkflowVersion, stages: list[StageDraft]
) -> None:
    """Этапы задаются целиком. Правила удаляются вместе с ними: они ссылаются на этапы."""
    codes = [stage.code for stage in stages]
    if len(set(codes)) != len(codes):
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Коды этапов повторяются.",
            errors=[FieldError(field="stages", message="Код этапа должен быть уникален")],
        )
    await _drop_transitions(session, draft.id)
    for stage in await session.scalars(select(Stage).where(Stage.version_id == draft.id)):
        await session.delete(stage)
    await session.flush()

    for stage_draft in stages:
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


async def _replace_transitions(
    session: AsyncSession, draft: WorkflowVersion, transitions: list[TransitionDraft]
) -> None:
    stages = {
        stage.code: stage
        for stage in await session.scalars(select(Stage).where(Stage.version_id == draft.id))
    }
    unknown = sorted(
        {
            code
            for rule in transitions
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
    await _drop_transitions(session, draft.id)
    for rule_draft in transitions:
        session.add(
            StageTransitionRule(
                version_id=draft.id,
                from_stage_id=stages[rule_draft.from_code].id,
                to_stage_id=stages[rule_draft.to_code].id,
                requires_comment=rule_draft.requires_comment,
                requires_attachment=rule_draft.requires_attachment,
            )
        )


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


@dataclass(slots=True)
class _PublishPlan:
    """Что сделает публикация. Предпросмотр и сама публикация считают это одинаково."""

    previous: WorkflowVersion | None
    old_stages: list[Stage]
    new_stages: dict[str, Stage]
    # Код этапа прежней схемы → код этапа новой, куда переедут его открытые записи.
    targets: dict[str, str]
    automatic: set[str]
    open_counts: dict[str, int]

    @property
    def renamed(self) -> list[tuple[Stage, Stage]]:
        return [
            (old, self.new_stages[old.code])
            for old in self.old_stages
            if old.code in self.new_stages and self.new_stages[old.code].name != old.name
        ]


def _neighbour(old_stages: list[Stage], index: int, new_stages: dict[str, Stage]) -> str:
    """Ближайший предыдущий этап прежней схемы, который остался; если такого нет — следующий.

    Предыдущий лучше следующего: вернуться на шаг безопаснее, чем проскочить этап,
    который может требовать документа.
    """
    for stage in reversed(old_stages[:index]):
        if stage.code in new_stages:
            return stage.code
    for stage in old_stages[index + 1 :]:
        if stage.code in new_stages:
            return stage.code
    # В новой схеме не осталось ни одного прежнего этапа: записи начинают с её первого этапа.
    return min(new_stages.values(), key=lambda stage: stage.position).code


async def _publish_plan(
    session: AsyncSession, draft: WorkflowVersion, payload: PublishRequest
) -> _PublishPlan:
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
    if previous is None:
        return _PublishPlan(None, [], new_stages, {}, set(), {})

    old_stages = list(
        await session.scalars(
            select(Stage).where(Stage.version_id == previous.id).order_by(Stage.position)
        )
    )
    old_codes = {stage.code for stage in old_stages}
    unknown = sorted(code for code in payload.migration_map if code not in old_codes)
    if unknown:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            f"В действующей схеме нет этапов: {', '.join(unknown)}.",
            errors=[
                FieldError(field=f"migration_map.{code}", message="Нет такого этапа")
                for code in unknown
            ],
        )
    invalid = sorted(
        code for code, target in payload.migration_map.items() if target not in new_stages
    )
    if invalid:
        raise AppError(
            ErrorCode.WF_MIGRATION_MAP_INCOMPLETE,
            f"Карта переносит записи на этапы, которых нет в новой схеме: {', '.join(invalid)}.",
            errors=[
                FieldError(field=f"migration_map.{code}", message="Нужен этап новой схемы")
                for code in invalid
            ],
        )

    targets: dict[str, str] = {}
    automatic: set[str] = set()
    for index, stage in enumerate(old_stages):
        if stage.code in payload.migration_map:
            targets[stage.code] = payload.migration_map[stage.code]
        elif stage.code in new_stages:
            targets[stage.code] = stage.code
        else:
            targets[stage.code] = _neighbour(old_stages, index, new_stages)
            automatic.add(stage.code)

    counts = await session.execute(
        select(Stage.code, func.count(Interaction.id))
        .select_from(Stage)
        .join(Interaction, Interaction.current_stage_id == Stage.id)
        .where(Stage.version_id == previous.id, Interaction.status.in_(OPEN_STATUSES))
        .group_by(Stage.code)
    )
    return _PublishPlan(
        previous, old_stages, new_stages, targets, automatic, dict(counts.tuples().all())
    )


def _preview(plan: _PublishPlan) -> PublishPreview:
    renamed = plan.renamed
    old_codes = {stage.code for stage in plan.old_stages}
    return PublishPreview(
        renamed=[
            StageRenameOut(code=old.code, old_name=old.name, new_name=new.name)
            for old, new in renamed
        ],
        moves=[
            StageMoveOut(
                from_code=stage.code,
                from_name=stage.name,
                stage_removed=stage.code not in plan.new_stages,
                open_interactions=plan.open_counts.get(stage.code, 0),
                to_code=plan.targets[stage.code],
                to_name=plan.new_stages[plan.targets[stage.code]].name,
                automatic=stage.code in plan.automatic,
            )
            for stage in plan.old_stages
            if plan.targets[stage.code] != stage.code
        ],
        added=[
            StageRef.model_validate(stage)
            for stage in sorted(plan.new_stages.values(), key=lambda item: item.position)
            if stage.code not in old_codes
        ],
        moved_interactions=sum(plan.open_counts.values()),
        requires_admin=bool(renamed),
    )


async def preview_publish(
    session: AsyncSession, version_id: uuid.UUID, payload: PublishRequest
) -> PublishPreview:
    """Ничего не меняет: показывает, что переименуется, что удалится и куда уйдут записи."""
    draft = await _draft(session, version_id)
    return _preview(await _publish_plan(session, draft, payload))


async def publish_version(
    session: AsyncSession,
    user: CurrentUser,
    version_id: uuid.UUID,
    payload: PublishRequest,
    trace_id: str | None = None,
    now: datetime | None = None,
) -> WorkflowVersion:
    """Публикует черновик и переводит на него открытые взаимодействия прежней схемы."""
    now = now or datetime.now(UTC)
    draft = await _draft(session, version_id)
    plan = await _publish_plan(session, draft, payload)
    renamed = plan.renamed
    if renamed and user.role is not Role.ADMIN:
        names = ", ".join(f"«{old.name}» → «{new.name}»" for old, new in renamed)
        raise AppError(
            ErrorCode.AUTH_FORBIDDEN,
            f"Черновик переименовывает этапы ({names}): опубликовать его может администратор.",
        )

    moved: list[uuid.UUID] = []
    if plan.previous is not None:
        moved = await _move_interactions(session, user, plan, plan.previous, draft, now)
        plan.previous.status = "retired"

    draft.status = "published"
    draft.published_at = now
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="workflow.version_published",
            entity_kind="workflow_version",
            entity_id=draft.id,
            before={"previous_version_id": str(plan.previous.id) if plan.previous else None},
            after={
                "version_no": draft.version_no,
                "moved_interactions": len(moved),
                "renamed": {old.code: new.name for old, new in renamed},
                "moves": {code: target for code, target in plan.targets.items() if code != target},
            },
            trace_id=trace_id,
        )
    )
    await session.flush()
    # Этап записи мог смениться, а с ним норма и требования к документам.
    await recompute_signals(session, moved, now)
    await mark_changed(session, moved, "workflow")
    await session.commit()
    return draft


async def _move_interactions(
    session: AsyncSession,
    user: CurrentUser,
    plan: _PublishPlan,
    previous: WorkflowVersion,
    draft: WorkflowVersion,
    now: datetime,
) -> list[uuid.UUID]:
    old_stages = {stage.id: stage for stage in plan.old_stages}
    interactions = list(
        await session.scalars(
            select(Interaction).where(
                Interaction.workflow_version_id == previous.id,
                Interaction.status.in_(OPEN_STATUSES),
            )
        )
    )
    moved_by_owner: dict[uuid.UUID, Counter[tuple[str, str]]] = defaultdict(Counter)
    for interaction in interactions:
        old = old_stages[interaction.current_stage_id]
        target = plan.new_stages[plan.targets[old.code]]
        if target.code != old.code:
            moved_by_owner[interaction.owner_user_id][(old.name, target.name)] += 1
        if target.code == old.code:
            comment = "Процесс обновлён"
        elif old.code in plan.new_stages:
            comment = f"Процесс обновлён: записи с этапа «{old.name}» перенесены на «{target.name}»"
        else:
            comment = f"Этап «{old.name}» удалён из процесса: запись перенесена на «{target.name}»"
        session.add(
            Transition(
                interaction_id=interaction.id,
                from_stage_id=interaction.current_stage_id,
                to_stage_id=target.id,
                occurred_at=now,
                actor_user_id=user.id,
                comment=comment,
                source="migration",
            )
        )
        if target.code != old.code:
            # Запись оказалась на другом этапе: дни считаются заново, иначе радар
            # сразу записал бы КАМу просрочку этапа, на который он её не ставил.
            interaction.stage_entered_at = now
        interaction.current_stage_id = target.id
        interaction.workflow_version_id = draft.id
        # Последняя активность не меняется: перенос схемы — не работа по взаимодействию.
        interaction.version += 1
    await session.flush()
    for owner_id, moves in moved_by_owner.items():
        if owner_id == user.id:
            continue
        total = sum(moves.values())
        lines = "; ".join(f"«{src}» → «{dst}»: {count}" for (src, dst), count in moves.items())
        await notify(
            session,
            [owner_id],
            "workflow_changed",
            f"Процесс изменён: записей на другом этапе — {total}",
            f"{user.full_name} опубликовал(а) изменения процесса. Этапы ваших записей: {lines}.",
            payload={"version_no": draft.version_no, "moved": total},
        )
    return [interaction.id for interaction in interactions]
