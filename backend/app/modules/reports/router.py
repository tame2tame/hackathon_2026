import uuid
from urllib.parse import quote

from fastapi import APIRouter, Request, Response, status
from fastapi.responses import StreamingResponse

from app.core.db import SessionDep
from app.core.errors import AppError, ErrorCode, error_responses
from app.core.http_cache import (
    NOT_MODIFIED,
    NOT_MODIFIED_RESPONSE,
    REVALIDATE,
    etag_of,
    fresh_for_client,
)
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
        **NOT_MODIFIED_RESPONSE,
    },
)
async def read_report_file(
    request: Request, report_id: uuid.UUID, session: SessionDep, user: CurrentUserDep
) -> Response:
    job = await get_job(session, user, report_id)
    if job.status != "done" or not job.file_key:
        raise AppError(ErrorCode.NOT_FOUND, "Файл ещё не готов.")
    # Готовый отчёт не перестраивается: тот же запуск — тот же файл.
    etag = etag_of(f"{job.id}:{job.finished_at}")
    # Файл не меняется, но доступ к нему может пропасть: браузер спрашивает сервер каждый раз.
    headers = {"ETag": etag, "Cache-Control": REVALIDATE}
    if fresh_for_client(request, etag):
        return Response(status_code=NOT_MODIFIED, headers=headers)
    file_name = f"Взаимодействия-{job.created_at:%Y-%m-%d}.{job.format}"
    media_type = MEDIA_TYPES[job.format]
    if job.format == "csv":
        media_type = f"{media_type}; charset={job.params.get('encoding', 'utf-8')}"
    headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(file_name)}"
    stream = await open_report_file(job)
    # Медленный клиент качает файл долго: база ему для этого не нужна, соединение — в пул.
    await session.close()
    return StreamingResponse(read_chunks(stream), media_type=media_type, headers=headers)
