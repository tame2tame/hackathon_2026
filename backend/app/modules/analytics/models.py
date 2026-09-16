"""Наборы весов рейтинга: сумма весов равна 100, один набор — по умолчанию."""

from sqlalchemy import CheckConstraint, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, Timestamps, UUIDPrimaryKey


class RatingWeightSet(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "rating_weight_set"
    __table_args__ = (
        CheckConstraint(
            "w_applications + w_students + w_streams = 100", name="weights_sum_to_hundred"
        ),
        CheckConstraint(
            "w_applications >= 0 AND w_students >= 0 AND w_streams >= 0", name="weights_positive"
        ),
        # Набор по умолчанию только один: частичный индекс не даёт завести второй.
        Index(
            "uq_rating_weight_set_default",
            "is_default",
            unique=True,
            postgresql_where=text("is_default"),
        ),
    )

    name: Mapped[str] = mapped_column(String(120), unique=True)
    w_applications: Mapped[int] = mapped_column(default=40, server_default=text("40"))
    w_students: Mapped[int] = mapped_column(default=40, server_default=text("40"))
    w_streams: Mapped[int] = mapped_column(default=20, server_default=text("20"))
    is_default: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
