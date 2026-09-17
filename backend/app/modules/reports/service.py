"""Отчёты: задание, его выполнение и выдача готового файла."""

import io
import uuid
from datetime import UTC, datetime
from typing import BinaryIO

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.core.events import REPORT_UPDATED, get_event_bus
from app.core.roles import Role
from app.core.security import CurrentUser
from app.core.storage import Storage, get_storage
from app.modules.interactions.service import InteractionFilters
from app.modules.reports import query, renderers
from app.modules.reports.models import ReportJob
from app.modules.reports.schemas import ReportCreate

JOB_NOT_FOUND = "Отчёт не найден."
TITLE = "Взаимодействия с вузами"


def filters_of(payload: ReportCreate) -> InteractionFilters:
    return InteractionFilters(
        group_id=payload.group_id,
        university_id=payload.university_id,
        direction_id=payload.direction_id,
        program_id=payload.program_id,
        product_id=payload.product_id,
        owner_id=payload.owner_id,
        stage_code=payload.stage_code,
        status=list(payload.status),
        period_from=payload.period_from,
        period_to=payload.period_to,
        search=payload.search.strip() if payload.search and payload.search.strip() else None,
    )


async def create_job(
    session: AsyncSession,
    user: CurrentUser,
    payload: ReportCreate,
    now: datetime | None = None,
) -> ReportJob:
    """Ставит задание в очередь. Слишком большой отчёт отклоняется сразу, а не после ожидания."""
    now = now or datetime.now(UTC)
    total = await query.count_rows(session, user, filters_of(payload), now)
    if total > query.MAX_ROWS:
        raise AppError(
            ErrorCode.REPORT_TOO_LARGE,
            f"Строк в отчёте {total} при пределе {query.MAX_ROWS}: сузьте период или фильтры.",
        )

    job = ReportJob(
        requested_by=user.id,
        params=payload.model_dump(mode="json"),
        format=payload.format,
        status="queued",
        progress=0,
        row_count=total,
    )
    session.add(job)
    await session.commit()
    return job


async def run_job(
    session: AsyncSession,
    user: CurrentUser,
    job_id: uuid.UUID,
    now: datetime | None = None,
    storage: Storage | None = None,
) -> ReportJob:
    """Строит файл отчёта. Область видимости берётся у того, кто заказал отчёт."""
    now = now or datetime.now(UTC)
    storage = storage or get_storage()
    job = await session.get(ReportJob, job_id)
    if job is None:
        raise AppError(ErrorCode.NOT_FOUND, JOB_NOT_FOUND)

    job.status = "running"
    job.progress = 10
    await session.commit()
    try:
        payload = ReportCreate.model_validate(job.params)
        rows = await query.build_rows(session, user, filters_of(payload), payload.columns, now)
        job.row_count = len(rows)
        job.progress = 60
        await session.commit()

        content = await run_in_threadpool(
            renderers.render,
            job.format,
            query.headers(payload.columns),
            rows,
            TITLE,
            payload.encoding,
        )
        job.file_key = f"reports/{job.id}.{job.format}"
        await run_in_threadpool(storage.save, job.file_key, io.BytesIO(content))
        job.status = "done"
        job.progress = 100
    except AppError as error:
        job.status, job.error_code = "failed", error.code.value
    except Exception:
        job.status, job.error_code = "failed", ErrorCode.INTERNAL_ERROR.value
        raise
    finally:
        job.finished_at = now
        await session.commit()
        await get_event_bus().publish(
            REPORT_UPDATED,
            {"report_id": str(job.id), "status": job.status, "progress": job.progress},
            owner_user_id=job.requested_by,
        )
    return job


async def enqueue_or_run(
    session: AsyncSession, user: CurrentUser, job: ReportJob, now: datetime | None = None
) -> ReportJob:
    """С Redis задание уходит воркеру, без него — строится сразу: демо работает одной командой."""
    settings = get_settings()
    if settings.app_env == "test" or not settings.redis_url:
        return await run_job(session, user, job.id, now)

    from arq import create_pool
    from arq.connections import RedisSettings

    pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    await pool.enqueue_job("build_report", str(job.id), str(user.id))
    return job


async def list_jobs(session: AsyncSession, user: CurrentUser) -> list[ReportJob]:
    jobs = await session.scalars(
        select(ReportJob)
        .where(ReportJob.requested_by == user.id)
        .order_by(ReportJob.created_at.desc())
        .limit(50)
    )
    return list(jobs)


async def get_job(session: AsyncSession, user: CurrentUser, job_id: uuid.UUID) -> ReportJob:
    job = await session.get(ReportJob, job_id)
    # Чужой отчёт может содержать данные вне области видимости, поэтому его просто нет.
    if job is None or (job.requested_by != user.id and user.role is not Role.ADMIN):
        raise AppError(ErrorCode.NOT_FOUND, JOB_NOT_FOUND)
    return job


async def open_report_file(
    session: AsyncSession, user: CurrentUser, job_id: uuid.UUID, storage: Storage | None = None
) -> tuple[ReportJob, BinaryIO]:
    storage = storage or get_storage()
    job = await get_job(session, user, job_id)
    if job.status != "done" or not job.file_key:
        raise AppError(ErrorCode.NOT_FOUND, "Файл ещё не готов.")
    try:
        stream = await run_in_threadpool(storage.open, job.file_key)
    except OSError as error:
        raise AppError(ErrorCode.NOT_FOUND, "Файл отчёта не найден.") from error
    return job, stream
