"""Схемы сигналов радара."""

import uuid
from datetime import datetime
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field

from app.modules.catalogs.schemas import ProductRef, ProgramRef, UniversityRef, UserRef
from app.modules.radar.messages import signal_message
from app.modules.radar.models import RadarSignal
from app.modules.radar.rules import Severity, SignalKind


class SignalOut(BaseModel):
    id: uuid.UUID
    kind: SignalKind
    severity: Severity
    detected_at: datetime
    resolved_at: datetime | None
    message: str = Field(description="Готовая строка для интерфейса, проверяемая по evidence")
    evidence: dict[str, Any] = Field(
        description=(
            "Доказательство сигнала: этап, дни на этапе, норма и её источник "
            "(norm_source: manual или suggested), дата окончания лицензии или последней активности"
        )
    )

    @classmethod
    def from_model(cls, signal: RadarSignal) -> Self:
        return cls(
            id=signal.id,
            kind=SignalKind(signal.kind),
            severity=Severity(signal.severity),
            detected_at=signal.detected_at,
            resolved_at=signal.resolved_at,
            message=signal_message(signal.kind, signal.evidence),
            evidence=signal.evidence,
        )


class InteractionRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    university: UniversityRef
    program: ProgramRef
    product: ProductRef
    owner: UserRef


class SignalListItem(SignalOut):
    interaction: InteractionRef


class SummaryRow(BaseModel):
    owner: UserRef
    counts: dict[SignalKind, int] = Field(description="Открытые сигналы по видам")
    total: int


class SignalSummaryOut(BaseModel):
    """Матрица «КАМ × вид сигнала» для тепловой карты руководителя."""

    kinds: list[SignalKind]
    rows: list[SummaryRow]
    total: int
