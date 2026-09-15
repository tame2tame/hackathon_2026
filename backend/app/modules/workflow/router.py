from fastapi import APIRouter

from app.core.db import SessionDep
from app.core.errors import ErrorCode, error_responses
from app.core.security import CurrentUserDep
from app.modules.workflow.schemas import WorkflowOut
from app.modules.workflow.service import get_default_workflow

router = APIRouter(prefix="/api/v1/workflows", tags=["workflow"])


@router.get(
    "/default",
    summary="Опубликованная версия базового workflow",
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND),
)
async def read_default_workflow(session: SessionDep, _user: CurrentUserDep) -> WorkflowOut:
    return await get_default_workflow(session)
