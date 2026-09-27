"""Интеграции: источники LMS и сайта, журнал обмена в обе стороны, заявки с сайта и outbox."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, Timestamps, UUIDPrimaryKey

SOURCE_KINDS = ("lms", "site")
RUN_STATUSES = ("running", "done", "failed")
MATCH_STATUSES = ("matched", "unmatched")
OUTBOX_STATUSES = ("pending", "sent", "failed")


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
    # Система принимает изменения записей CRM: обмен двусторонний.
    push_enabled: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    # Выключенный источник не синхронизируется по расписанию; вручную — можно.
    pull_enabled: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    last_push_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SyncRun(UUIDPrimaryKey, Base):
    """Запуск обмена: что и когда пришло или ушло, и почему не пришло или не ушло."""

    __tablename__ = "sync_run"
    __table_args__ = (
        CheckConstraint("status IN ('running', 'done', 'failed')", name="status"),
        CheckConstraint("direction IN ('pull', 'push')", name="direction"),
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("integration_source.id", ondelete="CASCADE"), index=True
    )
    direction: Mapped[str] = mapped_column(String(8), default="pull", server_default="pull")
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


class IntegrationOutbox(UUIDPrimaryKey, Base):
    """Запись CRM изменилась и ждёт отправки получателю. Пишется в транзакции самого изменения.

    Пока отправка не ушла, новые изменения той же записи не множат очередь, а увеличивают
    `change_seq`. Воркер захватывает строку арендой `locked_until`, а не блокировкой на время
    сетевого вызова, и отмечает отправку, только если `change_seq` не изменился: изменение,
    сделанное во время отправки, уйдёт следующим запуском, а не потеряется.
    """

    __tablename__ = "integration_outbox"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'sent', 'failed')", name="status"),
        Index(
            "uq_integration_outbox_pending",
            "source_id",
            "interaction_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
        Index("ix_integration_outbox_due", "status", "next_attempt_at"),
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("integration_source.id", ondelete="CASCADE")
    )
    interaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interaction.id", ondelete="RESTRICT"), index=True
    )
    reason: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(16), default="pending")
    change_seq: Mapped[int] = mapped_column(BigInteger, default=0, server_default=text("0"))
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    next_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_error: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
