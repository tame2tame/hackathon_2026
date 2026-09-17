import uuid
from urllib.parse import quote

from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse

from app.core.db import SessionDep
from app.core.errors import ErrorCode, error_responses
from app.core.security import CurrentUserDep
from app.modules.attachments.service import read_chunks
from app.modules.reports.renderers import MEDIA_TYPES
from app.modules.reports.schemas import COLUMNS, ReportCreate, ReportJobOut
from app.modules.reports.service import (
    create_job,
    enqueue_or_run,
    get_job,
    list_jobs,
    open_report_file,
)

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Заказать отчёт",
    description=(
        "Отчёт строится в фоне: ответ содержит id задания, дальше состояние смотрят "
        f"в `GET /api/v1/reports/{{id}}`. Колонки: {', '.join(COLUMNS)}."
    ),
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED, ErrorCode.VALIDATION_ERROR, ErrorCode.REPORT_TOO_LARGE
    ),
)
async def post_report(
    payload: ReportCreate, session: SessionDep, user: CurrentUserDep
) -> ReportJobOut:
    job = await create_job(session, user, payload)
    return ReportJobOut.model_validate(await enqueue_or_run(session, user, job))


@router.get(
    "",
    summary="Свои задания на отчёт",
    responses=error_responses(ErrorCode.AUTH_REQUIRED),
)
async def read_reports(session: SessionDep, user: CurrentUserDep) -> list[ReportJobOut]:
    return [ReportJobOut.model_validate(job) for job in await list_jobs(session, user)]


@router.get(
    "/{report_id}",
    summary="Состояние отчёта",
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND),
)
async def read_report(
    report_id: uuid.UUID, session: SessionDep, user: CurrentUserDep
) -> ReportJobOut:
    return ReportJobOut.model_validate(await get_job(session, user, report_id))


@router.get(
    "/{report_id}/file",
    summary="Скачать готовый отчёт",
    response_class=StreamingResponse,
    responses={
        200: {"content": {"application/octet-stream": {}}, "description": "Файл отчёта"},
        **error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND),
    },
)
async def read_report_file(
    report_id: uuid.UUID, session: SessionDep, user: CurrentUserDep
) -> StreamingResponse:
    job, stream = await open_report_file(session, user, report_id)
    file_name = f"Взаимодействия-{job.created_at:%Y-%m-%d}.{job.format}"
    media_type = MEDIA_TYPES[job.format]
    if job.format == "csv":
        media_type = f"{media_type}; charset={job.params.get('encoding', 'utf-8')}"
    return StreamingResponse(
        read_chunks(stream),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(file_name)}"},
    )
