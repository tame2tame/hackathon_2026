"""Подсказка нормы этапа по накопленной истории: медиана и 80-й перцентиль."""

from collections.abc import Sequence
from dataclasses import dataclass
from math import ceil
from statistics import median

# Меньше пяти наблюдений — подсказку не даём: случайность перевесит закономерность.
MIN_OBSERVATIONS = 5
SUGGESTION_SHARE = 0.8


@dataclass(frozen=True, slots=True)
class NormSuggestion:
    median_days: int
    percentile_days: int
    sample_size: int


def percentile(values: Sequence[int], share: float) -> int:
    """Метод ближайшего ранга: значение, которое не превышает заданная доля наблюдений."""
    if not values:
        raise ValueError("Нужно хотя бы одно наблюдение.")
    ordered = sorted(values)
    rank = min(len(ordered), max(1, ceil(share * len(ordered))))
    return ordered[rank - 1]


def suggest_norm(durations: Sequence[int]) -> NormSuggestion | None:
    """Подсказка по длительностям завершённых этапов в днях или None, если истории мало."""
    usable = [days for days in durations if days >= 0]
    if len(usable) < MIN_OBSERVATIONS:
        return None
    return NormSuggestion(
        median_days=int(median(usable)),
        percentile_days=percentile(usable, SUGGESTION_SHARE),
        sample_size=len(usable),
    )
