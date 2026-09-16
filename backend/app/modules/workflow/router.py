import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.core.db import SessionDep
from app.core.errors import ErrorCode, error_responses
from app.core.roles import Role
from app.core.security import CurrentUser, CurrentUserDep, require_roles
from app.modules.workflow.editor import (
    create_draft,
    create_template,
    patch_version,
    publish_version,
    rename_stage,
    version_out,
)
from app.modules.workflow.schemas import (
    NormUpdate,
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
    request: Request,
    session: SessionDep,
    user: ManagerDep,
) -> StageNormOut:
    trace_id = getattr(request.state, "trace_id", None)
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
    stage_code: str, request: Request, session: SessionDep, user: ManagerDep
) -> StageNormOut:
    trace_id = getattr(request.state, "trace_id", None)
    return await accept_suggestion(session, user, stage_code, trace_id=trace_id)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Создать шаблон процесса",
    responses=error_responses(*EDITOR_ERRORS),
)
async def post_template(
    payload: WorkflowTemplateCreate, request: Request, session: SessionDep, user: ManagerDep
) -> WorkflowTemplateOut:
    trace_id = getattr(request.state, "trace_id", None)
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
    template_id: uuid.UUID, request: Request, session: SessionDep, user: ManagerDep
) -> VersionOut:
    trace_id = getattr(request.state, "trace_id", None)
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
    request: Request,
    session: SessionDep,
    user: ManagerDep,
) -> VersionOut:
    trace_id = getattr(request.state, "trace_id", None)
    draft = await patch_version(session, user, version_id, payload, trace_id)
    return await version_out(session, draft)


@editor_router.patch(
    "/stages/{stage_id}",
    summary="Переименовать этап",
    description="Единственное изменение, разрешённое в опубликованной версии.",
    responses=error_responses(*EDITOR_ERRORS),
)
async def patch_stage(
    stage_id: uuid.UUID,
    payload: StageRename,
    request: Request,
    session: SessionDep,
    user: ManagerDep,
) -> StageRef:
    trace_id = getattr(request.state, "trace_id", None)
    stage = await rename_stage(session, user, stage_id, payload.name, trace_id)
    return StageRef.model_validate(stage)


@editor_router.post(
    "/workflow-versions/{version_id}/publish",
    summary="Опубликовать версию",
    description=(
        "Открытые взаимодействия переезжают на новую версию переходом `migration`, "
        "а прежняя версия становится `retired`. Карта переноса нужна для занятых этапов."
    ),
    responses=error_responses(
        *EDITOR_ERRORS, ErrorCode.WF_VERSION_NOT_DRAFT, ErrorCode.WF_MIGRATION_MAP_INCOMPLETE
    ),
)
async def post_publish(
    version_id: uuid.UUID,
    payload: PublishRequest,
    request: Request,
    session: SessionDep,
    user: ManagerDep,
) -> VersionOut:
    trace_id = getattr(request.state, "trace_id", None)
    published = await publish_version(session, user, version_id, payload, trace_id)
    return await version_out(session, published)
