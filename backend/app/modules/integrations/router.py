import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.db import SessionDep
from app.core.errors import ErrorCode, error_responses
from app.core.roles import Role
from app.core.security import CurrentUser, require_roles
from app.modules.integrations.schemas import (
    ApplicationMatch,
    IntegrationSourceOut,
    SiteApplicationOut,
    SyncRunOut,
)
from app.modules.integrations.service import (
    get_source,
    list_applications,
    list_runs,
    list_sources,
    match_application,
    sync_source,
)

router = APIRouter(prefix="/api/v1", tags=["integrations"])
ManagerDep = Annotated[CurrentUser, Depends(require_roles(Role.MANAGER, Role.ADMIN))]


@router.get(
    "/integrations",
    summary="Источники LMS и сайта",
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.AUTH_FORBIDDEN),
)
async def read_integrations(session: SessionDep, _user: ManagerDep) -> list[IntegrationSourceOut]:
    return [IntegrationSourceOut.model_validate(source) for source in await list_sources(session)]


@router.post(
    "/integrations/{source_id}/sync",
    summary="Синхронизировать источник вручную",
    description="Запись в журнале появляется и при отказе источника: там будет код ошибки.",
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED, ErrorCode.AUTH_FORBIDDEN, ErrorCode.NOT_FOUND
    ),
)
async def post_sync(source_id: uuid.UUID, session: SessionDep, _user: ManagerDep) -> SyncRunOut:
    source = await get_source(session, source_id)
    run = await sync_source(session, source)
    await session.commit()
    return SyncRunOut.model_validate(run)


@router.get(
    "/integrations/{source_id}/runs",
    summary="Журнал запусков источника",
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED, ErrorCode.AUTH_FORBIDDEN, ErrorCode.NOT_FOUND
    ),
)
async def read_runs(
    source_id: uuid.UUID, session: SessionDep, _user: ManagerDep
) -> list[SyncRunOut]:
    return [SyncRunOut.model_validate(run) for run in await list_runs(session, source_id)]


@router.get(
    "/site-applications",
    summary="Заявки с сайта",
    description="Без фильтра — все заявки; `match_status=unmatched` — очередь на разбор.",
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED, ErrorCode.AUTH_FORBIDDEN, ErrorCode.VALIDATION_ERROR
    ),
)
async def read_applications(
    session: SessionDep,
    _user: ManagerDep,
    match_status: Annotated[
        str | None, Query(pattern="^(matched|unmatched)$", description="Состояние сопоставления")
    ] = None,
) -> list[SiteApplicationOut]:
    applications = await list_applications(session, match_status)
    return [SiteApplicationOut.model_validate(application) for application in applications]


@router.post(
    "/site-applications/{application_id}/match",
    summary="Привязать заявку к взаимодействию",
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED, ErrorCode.AUTH_FORBIDDEN, ErrorCode.NOT_FOUND
    ),
)
async def post_match(
    application_id: uuid.UUID,
    payload: ApplicationMatch,
    session: SessionDep,
    user: ManagerDep,
) -> SiteApplicationOut:
    application = await match_application(session, user, application_id, payload.interaction_id)
    return SiteApplicationOut.model_validate(application)
