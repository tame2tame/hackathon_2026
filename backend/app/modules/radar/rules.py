"""Правила радара без обращения к БД (ARCHITECTURE.md, раздел 6). Покрываются юнит-тестами."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Any


class SignalKind(StrEnum):
    STAGE_OVERDUE = "stage_overdue"
    LICENSE_EXPIRING = "license_expiring"
    MISSING_DOCUMENT = "missing_document"
    INACTIVITY = "inactivity"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class RadarThresholds:
    license_warn_days: int = 60
    license_critical_days: int = 30
    inactivity_low_days: int = 21
    inactivity_medium_days: int = 42


DEFAULT_THRESHOLDS = RadarThresholds()


@dataclass(frozen=True, slots=True)
class InteractionState:
    """Всё, что нужно правилам, об одном взаимодействии в момент проверки."""

    status: str
    stage_code: str
    stage_name: str
    stage_kind: str
    stage_entered_at: datetime
    last_activity_at: datetime
    norm_days: int | None = None
    norm_source: str | None = None
    required_document_types: tuple[str, ...] = ()
    uploaded_document_types: frozenset[str] = frozenset()
    contract_number: str | None = None
    license_valid_until: date | None = None


@dataclass(frozen=True, slots=True)
class SignalDraft:
    kind: SignalKind
    severity: Severity
    evidence: dict[str, Any]


def evaluate_signals(
    state: InteractionState, now: datetime, thresholds: RadarThresholds = DEFAULT_THRESHOLDS
) -> list[SignalDraft]:
    """Возвращает сигналы, которые должны быть открыты для взаимодействия на момент `now`."""
    if state.status != "active":
        return []

    drafts: list[SignalDraft] = []
    days_on_stage = (now - state.stage_entered_at).days
    stage = {"stage_code": state.stage_code, "stage_name": state.stage_name}

    if state.norm_days and state.stage_kind != "final":
        if days_on_stage > state.norm_days:
            severity = Severity.HIGH if days_on_stage > 2 * state.norm_days else Severity.MEDIUM
            drafts.append(
                SignalDraft(
                    SignalKind.STAGE_OVERDUE,
                    severity,
                    {
                        **stage,
                        "days_on_stage": days_on_stage,
                        "norm_days": state.norm_days,
                        "norm_source": state.norm_source,
                        "stage_entered_at": state.stage_entered_at.isoformat(),
                    },
                )
            )
        missing = [
            doc for doc in state.required_document_types if doc not in state.uploaded_document_types
        ]
        # Документ подтверждает завершение этапа, поэтому предупреждаем после половины нормы.
        if missing and days_on_stage * 2 >= state.norm_days:
            drafts.append(
                SignalDraft(
                    SignalKind.MISSING_DOCUMENT,
                    Severity.MEDIUM,
                    {
                        **stage,
                        "days_on_stage": days_on_stage,
                        "norm_days": state.norm_days,
                        "norm_source": state.norm_source,
                        "missing_document_types": missing,
                    },
                )
            )

    if state.license_valid_until is not None:
        days_left = (state.license_valid_until - now.date()).days
        if days_left <= thresholds.license_warn_days:
            severity = (
                Severity.HIGH if days_left <= thresholds.license_critical_days else Severity.MEDIUM
            )
            drafts.append(
                SignalDraft(
                    SignalKind.LICENSE_EXPIRING,
                    severity,
                    {
                        "contract_number": state.contract_number,
                        "license_valid_until": state.license_valid_until.isoformat(),
                        "days_left": days_left,
                    },
                )
            )

    inactive_days = (now - state.last_activity_at).days
    if inactive_days >= thresholds.inactivity_low_days:
        severity = (
            Severity.MEDIUM if inactive_days >= thresholds.inactivity_medium_days else Severity.LOW
        )
        drafts.append(
            SignalDraft(
                SignalKind.INACTIVITY,
                severity,
                {
                    "inactive_days": inactive_days,
                    "last_activity_at": state.last_activity_at.isoformat(),
                    "threshold_days": thresholds.inactivity_low_days,
                },
            )
        )
    return drafts
