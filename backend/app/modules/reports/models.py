"""Задание на отчёт: параметры, ход выполнения и ключ готового файла."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, Timestamps, UUIDPrimaryKey

FORMATS = ("xlsx", "xls", "pdf", "json")
STATUSES = ("queued", "running", "done", "failed")


class ReportJob(UUIDPrimaryKey, Timestamps, Base):
    """Отчёт строится в фоне, поэтому у него есть состояние и прогресс."""

    __tablename__ = "report_job"
    __table_args__ = (
        CheckConstraint("status IN ('queued', 'running', 'done', 'failed')", name="status"),
        CheckConstraint("format IN ('xlsx', 'xls', 'pdf', 'json')", name="format"),
        CheckConstraint("progress BETWEEN 0 AND 100", name="progress"),
    )

    requested_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT"), index=True
    )
    # Период, фильтры и колонки — в том же виде, в каком их прислал клиент.
    params: Mapped[dict[str, Any]] = mapped_column(JSONB)
    format: Mapped[str] = mapped_column(String(8))
    status: Mapped[str] = mapped_column(String(16), default="queued")
    progress: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    row_count: Mapped[int | None]
    file_key: Mapped[str | None] = mapped_column(String(300))
    error_code: Mapped[str | None] = mapped_column(String(40))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
