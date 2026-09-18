"""Рейтинг востребованности (ARCHITECTURE.md, раздел 6): считается без обращения к БД.

Нормирование идёт внутри направления: сравнивать заявки на DevOps и на блокчейн бессмысленно,
а внутри одного направления 100 баллов получает лучший, остальные — долю от него.
"""

import uuid
from dataclasses import dataclass, field

METRICS = ("applications", "students", "streams")
DEFAULT_WEIGHTS: dict[str, int] = {"applications": 40, "students": 40, "streams": 20}
WEIGHTS_TOTAL = 100
FULL_SCORE = 100.0


@dataclass(frozen=True, slots=True)
class Entry:
    """Одна строка рейтинга до расчёта: значения метрик за период."""

    key: uuid.UUID
    name: str
    direction_id: uuid.UUID
    direction_name: str
    values: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Contribution:
    metric: str
    weight: int
    value: float
    normalized: float
    contribution: float


@dataclass(frozen=True, slots=True)
class RatingRow:
    place: int
    key: uuid.UUID
    name: str
    direction_name: str
    score: float
    contributions: list[Contribution]
    missing_metrics: list[str]

    @property
    def complete(self) -> bool:
        return not self.missing_metrics


def _maxima(entries: list[Entry]) -> dict[uuid.UUID, dict[str, float]]:
    """Максимум каждой метрики внутри направления — точка отсчёта для нормирования."""
    maxima: dict[uuid.UUID, dict[str, float]] = {}
    for entry in entries:
        inside = maxima.setdefault(entry.direction_id, dict.fromkeys(METRICS, 0.0))
        for metric in METRICS:
            value = entry.values.get(metric)
            if value is not None and value > inside[metric]:
                inside[metric] = value
    return maxima


def rate(entries: list[Entry], weights: dict[str, int] | None = None) -> list[RatingRow]:
    """Балл и вклад каждой метрики. Сумма вкладов равна баллу — это проверяется тестом."""
    weights = weights or DEFAULT_WEIGHTS
    maxima = _maxima(entries)
    rows: list[RatingRow] = []

    for entry in entries:
        inside = maxima[entry.direction_id]
        usable = [
            metric
            for metric in METRICS
            if entry.values.get(metric) is not None and inside[metric] > 0
        ]
        missing = [metric for metric in METRICS if metric not in usable]
        # Веса считаются только по имеющимся метрикам: недостающая не тянет балл вниз.
        weight_sum = sum(weights[metric] for metric in usable)
        contributions: list[Contribution] = []
        score = 0.0
        for metric in usable:
            value = entry.values[metric]
            normalized = FULL_SCORE * value / inside[metric]
            contribution = weights[metric] * normalized / weight_sum if weight_sum else 0.0
            score += contribution
            contributions.append(
                Contribution(
                    metric=metric,
                    weight=weights[metric],
                    value=value,
                    normalized=round(normalized, 2),
                    contribution=round(contribution, 2),
                )
            )
        rows.append(
            RatingRow(
                place=0,
                key=entry.key,
                name=entry.name,
                direction_name=entry.direction_name,
                score=round(score, 2),
                contributions=contributions,
                missing_metrics=missing,
            )
        )

    rows.sort(key=lambda row: (-row.score, row.name))
    return [
        RatingRow(
            place=index,
            key=row.key,
            name=row.name,
            direction_name=row.direction_name,
            score=row.score,
            contributions=row.contributions,
            missing_metrics=row.missing_metrics,
        )
        for index, row in enumerate(rows, start=1)
    ]


def normalize_weights(values: dict[str, int]) -> dict[str, int]:
    """Проверяет, что веса неотрицательны и дают в сумме 100."""
    weights = {metric: int(values.get(metric, 0)) for metric in METRICS}
    if any(weight < 0 for weight in weights.values()):
        raise ValueError("Вес не может быть отрицательным.")
    if sum(weights.values()) != WEIGHTS_TOTAL:
        raise ValueError(f"Сумма весов должна быть {WEIGHTS_TOTAL}.")
    return weights
