import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.db import SessionDep
from app.core.errors import ErrorCode, TraceIdDep, error_responses
from app.core.roles import Role
from app.core.security import CurrentUser, CurrentUserDep, require_roles
from app.modules.workflow.editor import (
    create_draft,
    create_template,
    patch_version,
    preview_publish,
    publish_version,
    rename_stage,
    version_out,
)
from app.modules.workflow.schemas import (
    NormUpdate,
    PublishPreview,
    PublishRequest,
    StageNormOut,
    StageRef,
    StageRename,
    VersionOut,
    VersionPatch,
    WorkflowOut,
    WorkflowTemplateCreate,
    WorkflowTemplateOut,
)
from app.modules.workflow.service import (
    accept_suggestion,
    get_default_workflow,
    list_norms,
    set_norm,
)

router = APIRouter(prefix="/api/v1/workflows", tags=["workflow"])
# Версии и этапы адресуются по своему идентификатору, поэтому живут вне префикса шаблонов.
editor_router = APIRouter(prefix="/api/v1", tags=["workflow"])
ManagerDep = Annotated[CurrentUser, Depends(require_roles(Role.MANAGER, Role.ADMIN))]
AdminDep = Annotated[CurrentUser, Depends(require_roles(Role.ADMIN))]
EDITOR_ERRORS = (
    ErrorCode.AUTH_REQUIRED,
    ErrorCode.AUTH_FORBIDDEN,
    ErrorCode.NOT_FOUND,
    ErrorCode.VALIDATION_ERROR,
)


@router.get(
    "/default",
    summary="Опубликованная версия базового workflow",
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND),
)
async def read_default_workflow(session: SessionDep, _user: CurrentUserDep) -> WorkflowOut:
    return await get_default_workflow(session)


@router.get(
    "/default/norms",
    summary="Нормы этапов с подсказками по истории",
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND),
)
async def read_norms(session: SessionDep, _user: CurrentUserDep) -> list[StageNormOut]:
    return await list_norms(session)


@router.put(
    "/default/norms/{stage_code}",
    summary="Задать норму этапа вручную",
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED,
        ErrorCode.AUTH_FORBIDDEN,
        ErrorCode.NOT_FOUND,
        ErrorCode.VALIDATION_ERROR,
    ),
)
async def put_norm(
    stage_code: str,
    payload: NormUpdate,
    trace_id: TraceIdDep,
    session: SessionDep,
    user: ManagerDep,
) -> StageNormOut:
    return await set_norm(session, user, stage_code, payload.norm_days, trace_id=trace_id)


@router.post(
    "/default/norms/{stage_code}/accept-suggestion",
    summary="Принять подсказку нормы",
    description="Нормой становится 80-й перцентиль завершённых этапов.",
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED,
        ErrorCode.AUTH_FORBIDDEN,
        ErrorCode.NOT_FOUND,
        ErrorCode.VALIDATION_ERROR,
    ),
)
async def post_accept_suggestion(
    stage_code: str, trace_id: TraceIdDep, session: SessionDep, user: ManagerDep
) -> StageNormOut:
    return await accept_suggestion(session, user, stage_code, trace_id=trace_id)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Создать шаблон процесса",
    responses=error_responses(*EDITOR_ERRORS),
)
async def post_template(
    payload: WorkflowTemplateCreate, trace_id: TraceIdDep, session: SessionDep, user: ManagerDep
) -> WorkflowTemplateOut:
    template = await create_template(session, user, payload.name, trace_id)
    return WorkflowTemplateOut.model_validate(template)


@router.post(
    "/{template_id}/versions",
    status_code=status.HTTP_201_CREATED,
    summary="Создать черновик версии",
    description="Черновик копирует последнюю версию шаблона: править проще, чем собирать заново.",
    responses=error_responses(*EDITOR_ERRORS),
)
async def post_version(
    template_id: uuid.UUID, trace_id: TraceIdDep, session: SessionDep, user: ManagerDep
) -> VersionOut:
    draft = await create_draft(session, user, template_id, trace_id)
    return await version_out(session, draft)


@editor_router.patch(
    "/workflow-versions/{version_id}",
    summary="Изменить черновик версии",
    description="Этапы, их порядок, нормы, требования к документам и правила переходов.",
    responses=error_responses(*EDITOR_ERRORS, ErrorCode.WF_VERSION_NOT_DRAFT),
)
async def patch_workflow_version(
    version_id: uuid.UUID,
    payload: VersionPatch,
    trace_id: TraceIdDep,
    session: SessionDep,
    user: ManagerDep,
) -> VersionOut:
    draft = await patch_version(session, user, version_id, payload, trace_id)
    return await version_out(session, draft)


@editor_router.patch(
    "/stages/{stage_id}",
    summary="Переименовать этап",
    description=(
        "Единственное изменение, разрешённое в действующей схеме. Переименование статуса — "
        "чувствительная операция, поэтому доступно только администратору."
    ),
    responses=error_responses(*EDITOR_ERRORS),
)
async def patch_stage(
    stage_id: uuid.UUID,
    payload: StageRename,
    trace_id: TraceIdDep,
    session: SessionDep,
    user: AdminDep,
) -> StageRef:
    stage = await rename_stage(session, user, stage_id, payload.name, trace_id)
    return StageRef.model_validate(stage)


@editor_router.post(
    "/workflow-versions/{version_id}/publish-preview",
    summary="Предпросмотр публикации",
    description=(
        "Ничего не меняет. Показывает переименованные и добавленные этапы, удалённые этапы "
        "с числом открытых записей и этапом, куда они переедут, и нужен ли администратор. "
        "Данные для окна подтверждения перед публикацией."
    ),
    responses=error_responses(
        *EDITOR_ERRORS, ErrorCode.WF_VERSION_NOT_DRAFT, ErrorCode.WF_MIGRATION_MAP_INCOMPLETE
    ),
)
async def post_publish_preview(
    version_id: uuid.UUID,
    payload: PublishRequest,
    session: SessionDep,
    _user: ManagerDep,
) -> PublishPreview:
    return await preview_publish(session, version_id, payload)


@editor_router.post(
    "/workflow-versions/{version_id}/publish",
    summary="Опубликовать изменения процесса",
    description=(
        "Все открытые взаимодействия переезжают на новую схему переходом `migration`, "
        "прежняя схема становится `retired`. Записи с удалённого этапа переходят на ближайший "
        "предыдущий этап, а если его нет — на следующий; `migration_map` задаёт другой этап явно. "
        "Черновик с переименованием этапов публикует только администратор."
    ),
    responses=error_responses(
        *EDITOR_ERRORS, ErrorCode.WF_VERSION_NOT_DRAFT, ErrorCode.WF_MIGRATION_MAP_INCOMPLETE
    ),
)
async def post_publish(
    version_id: uuid.UUID,
    payload: PublishRequest,
    trace_id: TraceIdDep,
    session: SessionDep,
    user: ManagerDep,
) -> VersionOut:
    published = await publish_version(session, user, version_id, payload, trace_id)
    return await version_out(session, published)
