import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.db import SessionDep
from app.core.errors import ErrorCode, error_responses
from app.core.pagination import Page, PageQuery
from app.core.security import CurrentUserDep
from app.modules.radar.rules import Severity, SignalKind
from app.modules.radar.schemas import SignalListItem, SignalSummaryOut
from app.modules.radar.service import SignalFilters, list_signals, signals_summary

router = APIRouter(prefix="/api/v1/signals", tags=["radar"])


def _signal_filters(
    group_id: Annotated[list[uuid.UUID] | None, Query(description="Группа контрагентов")] = None,
    kind: Annotated[list[SignalKind] | None, Query(description="Вид сигнала")] = None,
    severity: Annotated[list[Severity] | None, Query(description="Серьёзность")] = None,
    owner_id: Annotated[list[uuid.UUID] | None, Query(description="КАМ")] = None,
    university_id: Annotated[list[uuid.UUID] | None, Query(description="Вуз")] = None,
    period_from: Annotated[date | None, Query(description="Начало периода, UTC")] = None,
    period_to: Annotated[date | None, Query(description="Конец периода, UTC")] = None,
    search: Annotated[
        str | None, Query(max_length=100, description="Контрагент, программа или продукт")
    ] = None,
) -> SignalFilters:
    return SignalFilters(
        group_id=group_id or [],
        kind=[k.value for k in kind or []],
        severity=[s.value for s in severity or []],
        owner_id=owner_id or [],
        university_id=university_id or [],
        period_from=period_from,
        period_to=period_to,
        search=search.strip() if search and search.strip() else None,
    )


@router.get(
    "",
    summary="Открытые сигналы радара",
    description="Сначала высокая серьёзность, затем самые свежие. Учитывает область видимости.",
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.VALIDATION_ERROR),
)
async def read_signals(
    session: SessionDep,
    user: CurrentUserDep,
    page: PageQuery,
    filters: Annotated[SignalFilters, Depends(_signal_filters)],
) -> Page[SignalListItem]:
    return await list_signals(session, user, filters, page)


@router.get(
    "/summary",
    summary="Матрица «КАМ × вид сигнала»",
    description="Тепловая карта руководителя: открытые сигналы по видам у каждого КАМа.",
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.VALIDATION_ERROR),
)
async def read_signals_summary(
    session: SessionDep,
    user: CurrentUserDep,
    filters: Annotated[SignalFilters, Depends(_signal_filters)],
) -> SignalSummaryOut:
    return await signals_summary(session, user, filters)
