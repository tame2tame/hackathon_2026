"""Сигналы радара: проблема взаимодействия с объяснением причины."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, UUIDPrimaryKey


class RadarSignal(UUIDPrimaryKey, Base):
    __tablename__ = "radar_signal"
    __table_args__ = (
        # Не больше одного открытого сигнала каждого вида на взаимодействие.
        Index(
            "uq_radar_signal_open",
            "interaction_id",
            "kind",
            unique=True,
            postgresql_where=text("resolved_at IS NULL"),
        ),
        CheckConstraint(
            "kind IN ('stage_overdue', 'license_expiring', 'missing_document', 'inactivity')",
            name="kind",
        ),
        CheckConstraint("severity IN ('low', 'medium', 'high')", name="severity"),
    )

    interaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interaction.id", ondelete="RESTRICT"), index=True
    )
    kind: Mapped[str] = mapped_column(String(32))
    severity: Mapped[str] = mapped_column(String(16))
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Всё, что нужно для ручной проверки сигнала: этап, дни, норма, даты.
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB)
