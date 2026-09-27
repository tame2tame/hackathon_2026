import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core import cache
from app.core.db import SessionDep
from app.core.errors import ErrorCode, TraceIdDep, error_responses
from app.core.roles import Role
from app.core.security import CurrentUser, require_roles
from app.modules.audit.models import AuditLog
from app.modules.integrations.outbox import list_outbox, push_source
from app.modules.integrations.schemas import (
    ApplicationMatch,
    IntegrationSourceOut,
    OutboxEntryOut,
    SiteApplicationOut,
    SourceUpdate,
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
AdminDep = Annotated[CurrentUser, Depends(require_roles(Role.ADMIN))]


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
    await cache.invalidate(cache.RATING)
    return SyncRunOut.model_validate(run)


@router.patch(
    "/integrations/{source_id}",
    summary="Включить или выключить отправку изменений источнику",
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED,
        ErrorCode.AUTH_FORBIDDEN,
        ErrorCode.NOT_FOUND,
        ErrorCode.VALIDATION_ERROR,
    ),
)
async def patch_source(
    source_id: uuid.UUID,
    payload: SourceUpdate,
    trace_id: TraceIdDep,
    session: SessionDep,
    admin: AdminDep,
) -> IntegrationSourceOut:
    source = await get_source(session, source_id)
    before = {"push_enabled": source.push_enabled, "pull_enabled": source.pull_enabled}
    if payload.push_enabled is not None:
        source.push_enabled = payload.push_enabled
    if payload.pull_enabled is not None:
        source.pull_enabled = payload.pull_enabled
    session.add(
        AuditLog(
            actor_user_id=admin.id,
            action="integration.source_changed",
            entity_kind="integration_source",
            entity_id=source.id,
            before=before,
            after={"push_enabled": source.push_enabled, "pull_enabled": source.pull_enabled},
            trace_id=trace_id,
        )
    )
    await session.commit()
    return IntegrationSourceOut.model_validate(source)


@router.post(
    "/integrations/{source_id}/push",
    summary="Отправить изменения записей в систему сейчас",
    description=(
        "То же, что делает воркер раз в минуту: документы `radar-vuzov/interaction@1` по записям "
        "из очереди уходят одним пакетом. Запуск пишется в журнал с направлением `push`, "
        "отказ получателя — с кодом `INTEGRATION_UNAVAILABLE` и повтором позже."
    ),
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED, ErrorCode.AUTH_FORBIDDEN, ErrorCode.NOT_FOUND
    ),
)
async def post_push(source_id: uuid.UUID, session: SessionDep, _user: ManagerDep) -> SyncRunOut:
    source = await get_source(session, source_id)
    run = await push_source(session, source)
    await session.commit()
    return SyncRunOut.model_validate(run)


@router.get(
    "/integrations/{source_id}/outbox",
    summary="Очередь отправки источнику",
    description="Какие записи ждут отправки, ушли или отклонены получателем и почему.",
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED,
        ErrorCode.AUTH_FORBIDDEN,
        ErrorCode.NOT_FOUND,
        ErrorCode.VALIDATION_ERROR,
    ),
)
async def read_outbox(
    source_id: uuid.UUID,
    session: SessionDep,
    _user: ManagerDep,
    status: Annotated[
        str | None, Query(pattern="^(pending|sent|failed)$", description="Состояние отправки")
    ] = None,
) -> list[OutboxEntryOut]:
    await get_source(session, source_id)
    entries = await list_outbox(session, source_id, status)
    return [OutboxEntryOut.model_validate(entry) for entry in entries]


@router.get(
    "/integrations/{source_id}/runs",
    summary="Журнал обмена с источником в обе стороны",
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
