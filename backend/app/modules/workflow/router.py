from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.db import SessionDep
from app.core.errors import ErrorCode, error_responses
from app.core.roles import Role
from app.core.security import CurrentUser, CurrentUserDep, require_roles
from app.modules.workflow.schemas import NormUpdate, StageNormOut, WorkflowOut
from app.modules.workflow.service import (
    accept_suggestion,
    get_default_workflow,
    list_norms,
    set_norm,
)

router = APIRouter(prefix="/api/v1/workflows", tags=["workflow"])
ManagerDep = Annotated[CurrentUser, Depends(require_roles(Role.MANAGER, Role.ADMIN))]


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
