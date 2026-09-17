from datetime import UTC, date, datetime, timedelta

import pytest

from app.modules.radar.messages import plural_days, signal_message
from app.modules.radar.rules import InteractionState, Severity, SignalKind, evaluate_signals

NOW = datetime(2026, 9, 15, 9, 0, tzinfo=UTC)


def state(**overrides: object) -> InteractionState:
    values: dict[str, object] = {
        "status": "active",
        "stage_code": "signing",
        "stage_name": "Подписание",
        "stage_kind": "normal",
        "stage_entered_at": NOW - timedelta(days=3),
        "last_activity_at": NOW - timedelta(days=1),
        "norm_days": 14,
    }
    values.update(overrides)
    return InteractionState(**values)  # type: ignore[arg-type]


def kinds(drafts: list) -> dict[SignalKind, Severity]:  # type: ignore[type-arg]
    return {draft.kind: draft.severity for draft in drafts}


@pytest.mark.parametrize(
    ("days", "expected"),
    [(14, None), (15, Severity.MEDIUM), (28, Severity.MEDIUM), (29, Severity.HIGH)],
)
def test_stage_overdue_severity(days: int, expected: Severity | None) -> None:
    drafts = evaluate_signals(state(stage_entered_at=NOW - timedelta(days=days)), NOW)

    assert kinds(drafts).get(SignalKind.STAGE_OVERDUE) == expected


def test_final_stage_is_never_overdue() -> None:
    drafts = evaluate_signals(
        state(stage_kind="final", stage_entered_at=NOW - timedelta(days=400)), NOW
    )

    assert SignalKind.STAGE_OVERDUE not in kinds(drafts)


@pytest.mark.parametrize(
    ("days_left", "expected"),
    [
        (61, None),
        (60, Severity.MEDIUM),
        (31, Severity.MEDIUM),
        (30, Severity.HIGH),
        (-2, Severity.HIGH),
    ],
)
def test_license_expiring_severity(days_left: int, expected: Severity | None) -> None:
    drafts = evaluate_signals(
        state(contract_number="Д-1", license_valid_until=NOW.date() + timedelta(days=days_left)),
        NOW,
    )

    assert kinds(drafts).get(SignalKind.LICENSE_EXPIRING) == expected


def test_missing_document_after_half_of_norm() -> None:
    required = ("signed_contract",)
    early = state(stage_entered_at=NOW - timedelta(days=6), required_document_types=required)
    due = state(stage_entered_at=NOW - timedelta(days=7), required_document_types=required)
    uploaded = state(
        stage_entered_at=NOW - timedelta(days=7),
        required_document_types=required,
        uploaded_document_types=frozenset(required),
    )

    assert SignalKind.MISSING_DOCUMENT not in kinds(evaluate_signals(early, NOW))
    assert kinds(evaluate_signals(due, NOW))[SignalKind.MISSING_DOCUMENT] is Severity.MEDIUM
    assert SignalKind.MISSING_DOCUMENT not in kinds(evaluate_signals(uploaded, NOW))


@pytest.mark.parametrize(
    ("inactive", "expected"), [(13, None), (14, Severity.LOW), (28, Severity.MEDIUM)]
)
def test_inactivity_severity(inactive: int, expected: Severity | None) -> None:
    drafts = evaluate_signals(state(last_activity_at=NOW - timedelta(days=inactive)), NOW)

    assert kinds(drafts).get(SignalKind.INACTIVITY) == expected


def test_inactive_interaction_has_no_signals() -> None:
    drafts = evaluate_signals(
        state(status="paused", stage_entered_at=NOW - timedelta(days=100)), NOW
    )

    assert drafts == []


@pytest.mark.parametrize(
    ("n", "word"), [(1, "день"), (2, "дня"), (5, "дней"), (11, "дней"), (21, "день"), (23, "дня")]
)
def test_plural_days(n: int, word: str) -> None:
    assert plural_days(n) == word


def test_messages_can_be_checked_by_hand() -> None:
    overdue = signal_message(
        "stage_overdue",
        {
            "days_on_stage": 41,
            "norm_days": 14,
            "stage_name": "Подписание",
            "norm_source": "manual",
        },
    )
    license_message = signal_message(
        "license_expiring",
        {
            "contract_number": "Д-2026/042",
            "license_valid_until": date(2026, 10, 4).isoformat(),
            "days_left": 19,
        },
    )

    assert overdue == "41 день на этапе «Подписание» при норме 14 дней. Норма задана вручную."
    assert license_message == "Лицензия по договору Д-2026/042 истекает 04.10.2026 — через 19 дней."
