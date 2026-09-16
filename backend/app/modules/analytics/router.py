import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.core.db import SessionDep
from app.core.errors import AppError, ErrorCode, error_responses
from app.core.roles import Role
from app.core.security import CurrentUser, CurrentUserDep, require_roles
from app.modules.analytics import stats
from app.modules.analytics.rating import normalize_weights
from app.modules.analytics.schemas import (
    ChartOut,
    RatingEntity,
    RatingOut,
    WeightsOut,
    WeightsUpdate,
)
from app.modules.analytics.service import ensure_default_weights, rating, set_weights

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])
ManagerDep = Annotated[CurrentUser, Depends(require_roles(Role.MANAGER, Role.ADMIN))]


def _weights_from_query(
    w_applications: int | None, w_students: int | None, w_streams: int | None
) -> dict[str, int] | None:
    """Веса из запроса: руководитель крутит ползунки и сразу видит другой порядок."""
    given = (w_applications, w_students, w_streams)
    if all(value is None for value in given):
        return None
    try:
        return normalize_weights(
            {
                "applications": w_applications or 0,
                "students": w_students or 0,
                "streams": w_streams or 0,
            }
        )
    except ValueError as error:
        raise AppError(ErrorCode.VALIDATION_ERROR, str(error)) from error


@router.get(
    "/rating",
    summary="Рейтинг востребованности",
    description=(
        "Балл считается по заявкам, обучающимся и потокам с нормированием внутри направления. "
        "Вклад каждой метрики возвращается вместе с баллом, а неполные данные помечаются."
    ),
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.VALIDATION_ERROR),
)
async def read_rating(
    session: SessionDep,
    _user: CurrentUserDep,
    entity: Annotated[RatingEntity, Query(description="Что сравниваем")] = "program",
    period_from: Annotated[date | None, Query(description="Начало периода")] = None,
    period_to: Annotated[date | None, Query(description="Конец периода")] = None,
    direction_id: Annotated[list[uuid.UUID] | None, Query(description="ИТ-направление")] = None,
    w_applications: Annotated[int | None, Query(ge=0, le=100)] = None,
    w_students: Annotated[int | None, Query(ge=0, le=100)] = None,
    w_streams: Annotated[int | None, Query(ge=0, le=100)] = None,
) -> RatingOut:
    weights = _weights_from_query(w_applications, w_students, w_streams)
    return await rating(session, entity, period_from, period_to, direction_id or [], weights)


@router.get(
    "/rating/weights",
    summary="Веса рейтинга по умолчанию",
    responses=error_responses(ErrorCode.AUTH_REQUIRED),
)
async def read_weights(session: SessionDep, _user: CurrentUserDep) -> WeightsOut:
    weights = await ensure_default_weights(session)
    await session.commit()
    return WeightsOut.model_validate(weights)


@router.put(
    "/rating/weights",
    summary="Изменить веса рейтинга",
    description="Сумма весов — 100. Меняют руководитель и администратор.",
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED, ErrorCode.AUTH_FORBIDDEN, ErrorCode.VALIDATION_ERROR
    ),
)
async def put_weights(
    payload: WeightsUpdate, request: Request, session: SessionDep, user: ManagerDep
) -> WeightsOut:
    trace_id = getattr(request.state, "trace_id", None)
    return WeightsOut.model_validate(await set_weights(session, user, payload, trace_id))


@router.get(
    "/stats/funnel",
    summary="Воронка по этапам",
    responses=error_responses(ErrorCode.AUTH_REQUIRED),
)
async def read_funnel(session: SessionDep, user: CurrentUserDep) -> ChartOut:
    return await stats.funnel(session, user)


@router.get(
    "/stats/stage-durations",
    summary="Средняя длительность этапов",
    responses=error_responses(ErrorCode.AUTH_REQUIRED),
)
async def read_stage_durations(session: SessionDep, user: CurrentUserDep) -> ChartOut:
    return await stats.stage_durations(session, user)


@router.get(
    "/stats/distribution",
    summary="Распределение по направлениям",
    responses=error_responses(ErrorCode.AUTH_REQUIRED),
)
async def read_distribution(session: SessionDep, user: CurrentUserDep) -> ChartOut:
    return await stats.distribution(session, user)
