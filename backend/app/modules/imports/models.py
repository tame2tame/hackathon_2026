"""Импорт выгрузок заказчика: профиль соответствия колонок, партия и её строки."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, Timestamps, UUIDPrimaryKey

RESOLUTIONS = ("new", "update", "conflict", "skip", "needs_program")
STATUSES = ("uploaded", "previewed", "applied", "failed")


class ImportProfile(UUIDPrimaryKey, Timestamps, Base):
    """Сохранённое соответствие колонок: следующий импорт идёт без ручной настройки."""

    __tablename__ = "import_profile"
    __table_args__ = (CheckConstraint("file_kind IN ('xls', 'xlsx', 'csv')", name="file_kind"),)

    name: Mapped[str] = mapped_column(String(200), unique=True)
    file_kind: Mapped[str] = mapped_column(String(8))
    column_map: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class ImportBatch(UUIDPrimaryKey, Timestamps, Base):
    """Одна загрузка файла: от разбора до применения."""

    __tablename__ = "import_batch"
    __table_args__ = (
        CheckConstraint("status IN ('uploaded', 'previewed', 'applied', 'failed')", name="status"),
    )

    profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("import_profile.id", ondelete="SET NULL")
    )
    file_name: Mapped[str] = mapped_column(String(255))
    file_kind: Mapped[str] = mapped_column(String(8))
    # Кодировка и разделитель, с которыми прочитан CSV: видны в предпросмотре вместе с данными.
    encoding: Mapped[str | None] = mapped_column(String(20))
    delimiter: Mapped[str | None] = mapped_column(String(1))
    status: Mapped[str] = mapped_column(String(16), default="uploaded")
    # Заголовки файла и выбранное соответствие храним здесь: файл после разбора не нужен.
    headers: Mapped[list[str]] = mapped_column(JSONB, default=list)
    column_map: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    stats: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_user.id", ondelete="RESTRICT"))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ImportRow(UUIDPrimaryKey, Base):
    """Строка файла как она прочитана, и что с ней решено сделать."""

    __tablename__ = "import_row"
    __table_args__ = (
        Index("uq_import_row_batch_row_no", "batch_id", "row_no", unique=True),
        CheckConstraint(
            "resolution IN ('new', 'update', 'conflict', 'skip', 'needs_program')",
            name="resolution",
        ),
    )

    batch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("import_batch.id", ondelete="CASCADE"))
    row_no: Mapped[int]
    raw: Mapped[dict[str, Any]] = mapped_column(JSONB)
    resolution: Mapped[str] = mapped_column(String(16), default="new")
    detail: Mapped[str | None] = mapped_column(Text)
