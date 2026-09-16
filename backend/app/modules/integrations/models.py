"""Интеграции: источники LMS и сайта, журнал запусков и заявки с сайта."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, Timestamps, UUIDPrimaryKey

SOURCE_KINDS = ("lms", "site")
RUN_STATUSES = ("running", "done", "failed")
MATCH_STATUSES = ("matched", "unmatched")


class IntegrationSource(UUIDPrimaryKey, Timestamps, Base):
    """Внешняя система, из которой приходят метрики и заявки."""

    __tablename__ = "integration_source"
    __table_args__ = (CheckConstraint("kind IN ('lms', 'site')", name="kind"),)

    kind: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(120), unique=True)
    base_url: Mapped[str] = mapped_column(String(300))
    # Сам секрет живёт в переменных окружения; здесь только имя переменной.
    secret_ref: Mapped[str | None] = mapped_column(String(120))
    is_mock: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    schedule_cron: Mapped[str | None] = mapped_column(String(60))
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SyncRun(UUIDPrimaryKey, Base):
    """Запуск синхронизации: по нему видно, что и когда пришло, и почему не пришло."""

    __tablename__ = "sync_run"
    __table_args__ = (CheckConstraint("status IN ('running', 'done', 'failed')", name="status"),)

    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("integration_source.id", ondelete="CASCADE"), index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), default="running")
    stats: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    error_code: Mapped[str | None] = mapped_column(String(40))


class SiteApplication(UUIDPrimaryKey, Timestamps, Base):
    """Заявка с сайта: либо привязана к взаимодействию, либо ждёт решения человека."""

    __tablename__ = "site_application"
    __table_args__ = (
        CheckConstraint("match_status IN ('matched', 'unmatched')", name="match_status"),
    )

    external_id: Mapped[str] = mapped_column(String(120), unique=True)
    university_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("university.id", ondelete="RESTRICT"), index=True
    )
    program_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("program.id", ondelete="RESTRICT")
    )
    # Как заявка пришла: названия из формы сайта, которые могли не найтись в справочниках.
    university_name: Mapped[str] = mapped_column(String(300))
    program_name: Mapped[str] = mapped_column(String(300))
    contact_name: Mapped[str | None] = mapped_column(String(200))
    comment: Mapped[str | None] = mapped_column(String(2000))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    match_status: Mapped[str] = mapped_column(String(16), default="unmatched")
    interaction_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("interaction.id", ondelete="SET NULL")
    )
