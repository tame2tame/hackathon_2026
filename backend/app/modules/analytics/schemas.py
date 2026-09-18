"""Схемы рейтинга и статистики."""

import uuid
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.analytics.rating import WEIGHTS_TOTAL

RatingEntity = Literal["program", "university"]
RatingOrder = Literal["score", "priority"]


class ContributionOut(BaseModel):
    metric: str = Field(description="applications, students или streams")
    weight: int
    value: float = Field(description="Значение метрики за период")
    normalized: float = Field(description="Доля от лучшего в направлении, 0–100")
    contribution: float = Field(description="Вклад метрики в балл")


class RatingRowOut(BaseModel):
    place: int
    place_change: int | None = Field(
        description="Насколько поднялась позиция к предыдущему периоду; null — раньше её не было"
    )
    id: uuid.UUID
    name: str
    direction_name: str
    score: float
    priority: int = Field(description="Ручной приоритет курса, 0 — не задан")
    contributions: list[ContributionOut]
    complete: bool = Field(description="Есть ли все три метрики за период")
    missing_metrics: list[str]


class RatingOut(BaseModel):
    entity: RatingEntity
    weights: dict[str, int]
    order: RatingOrder = Field(
        default="score", description="Чем отсортированы строки: баллом или ручным приоритетом"
    )
    rows: list[RatingRowOut]


class WeightsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    w_applications: int
    w_students: int
    w_streams: int
    is_default: bool


class WeightsUpdate(BaseModel):
    w_applications: int = Field(ge=0, le=WEIGHTS_TOTAL)
    w_students: int = Field(ge=0, le=WEIGHTS_TOTAL)
    w_streams: int = Field(ge=0, le=WEIGHTS_TOTAL)

    @model_validator(mode="after")
    def check_sum(self) -> Self:
        if self.w_applications + self.w_students + self.w_streams != WEIGHTS_TOTAL:
            raise ValueError(f"Сумма весов должна быть {WEIGHTS_TOTAL}")
        return self


class ChartOut(BaseModel):
    """Данные и настройки ECharts: интерфейс и PDF рисуют график по одному описанию."""

    title: str
    labels: list[str]
    values: list[int]
    option: dict[str, Any] = Field(description="Готовые настройки ECharts")


class StatsOut(BaseModel):
    funnel: ChartOut
    stage_durations: ChartOut
    distribution: ChartOut
