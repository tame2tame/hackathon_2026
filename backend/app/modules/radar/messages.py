"""Текст сигнала для интерфейса: одна строка, которую эксперт может перепроверить по данным."""

from datetime import date
from typing import Any

from app.modules.radar.rules import SignalKind

DOCUMENT_LABELS = {
    "signed_contract": "подписанный договор",
    "transfer_act": "акт передачи",
    "training_confirmation": "подтверждение обучения",
}


def plural_days(n: int) -> str:
    tail = abs(n) % 100
    if 11 <= tail <= 14:
        return "дней"
    match tail % 10:
        case 1:
            return "день"
        case 2 | 3 | 4:
            return "дня"
        case _:
            return "дней"


def _days(n: int) -> str:
    return f"{n} {plural_days(n)}"


def _ru_date(iso: str) -> str:
    return date.fromisoformat(iso[:10]).strftime("%d.%m.%Y")


def signal_message(kind: str, evidence: dict[str, Any]) -> str:
    match SignalKind(kind):
        case SignalKind.STAGE_OVERDUE:
            return (
                f"{_days(evidence['days_on_stage']).capitalize()} на этапе "
                f"«{evidence['stage_name']}» при норме {_days(evidence['norm_days'])}."
            )
        case SignalKind.LICENSE_EXPIRING:
            valid_until = _ru_date(evidence["license_valid_until"])
            contract = evidence.get("contract_number") or "без номера"
            days_left = int(evidence["days_left"])
            if days_left < 0:
                return f"Лицензия по договору {contract} истекла {valid_until}."
            return (
                f"Лицензия по договору {contract} истекает {valid_until} — "
                f"через {_days(days_left)}."
            )
        case SignalKind.MISSING_DOCUMENT:
            documents = ", ".join(
                DOCUMENT_LABELS.get(doc, doc) for doc in evidence["missing_document_types"]
            )
            return (
                f"На этапе «{evidence['stage_name']}» нет документа: {documents}. "
                f"Этап длится {_days(evidence['days_on_stage'])} из {evidence['norm_days']}."
            )
        case SignalKind.INACTIVITY:
            return (
                f"Нет активности {_days(evidence['inactive_days'])}: последнее действие "
                f"{_ru_date(evidence['last_activity_at'])}, порог — "
                f"{_days(evidence['threshold_days'])}."
            )
