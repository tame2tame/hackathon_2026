"""Месячные показатели программы в вузе: заявки, обучающиеся, потоки (ТЗ, раздел показателей)."""

import uuid
from datetime import date

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, Timestamps, UUIDPrimaryKey

METRIC_KINDS = ("applications", "students", "streams")


class ProgramMetric(UUIDPrimaryKey, Timestamps, Base):
    """Одно значение за месяц. По этим трём метрикам считается индекс спроса в рейтинге."""

    __tablename__ = "program_metric"
    __table_args__ = (
        # Источник входит в ключ: LMS и сайт считают разные метрики и не затирают друг друга.
        UniqueConstraint("university_id", "program_id", "period_month", "metric", "source"),
        CheckConstraint("metric IN ('applications', 'students', 'streams')", name="metric"),
        CheckConstraint("source IN ('lms', 'site', 'manual', 'demo')", name="source"),
        CheckConstraint("value >= 0", name="value_not_negative"),
    )

    university_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("university.id", ondelete="RESTRICT"), index=True
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("program.id", ondelete="RESTRICT"), index=True
    )
    # Первое число месяца: период хранится датой, чтобы фильтры работали без разбора строк.
    period_month: Mapped[date]
    metric: Mapped[str] = mapped_column(String(16))
    value: Mapped[int]
    source: Mapped[str] = mapped_column(String(16), default="demo")
