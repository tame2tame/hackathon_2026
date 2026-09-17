"""Уведомления: в интерфейсе, каналы доставки (Telegram, Max, почта), адреса и журнал."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, UUIDPrimaryKey

NOTIFICATION_KINDS = ("stalled_interaction", "stage_changed", "workflow_changed", "channel_test")
CHANNEL_KINDS = ("telegram", "max", "email")
DELIVERY_STATUSES = ("pending", "sent", "failed")


class Notification(UUIDPrimaryKey, Base):
    """Уведомление сотруднику. Видно в интерфейсе и, если он подписан, уходит в каналы."""

    __tablename__ = "notification"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('stalled_interaction', 'stage_changed', 'workflow_changed', 'channel_test')",
            name="kind",
        ),
        Index("ix_notification_user_created", "user_id", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_user.id", ondelete="RESTRICT"))
    kind: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    interaction_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("interaction.id", ondelete="RESTRICT")
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    # Одно событие не уведомляет дважды: например, один эпизод простоя записи.
    dedupe_key: Mapped[str | None] = mapped_column(String(200), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class NotificationChannel(Base):
    """Канал доставки. Токены и пароли живут в окружении: здесь только имя переменной."""

    __tablename__ = "notification_channel"
    __table_args__ = (CheckConstraint("kind IN ('telegram', 'max', 'email')", name="kind"),)

    kind: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    is_enabled: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    is_mock: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    # Адрес API мессенджера или почтового сервера и прочие несекретные параметры.
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    secret_ref: Mapped[str | None] = mapped_column(String(120))
    # Какие виды уведомлений канал пересылает.
    kinds: Mapped[list[str]] = mapped_column(ARRAY(String(40)), default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL")
    )


class NotificationAddress(Base):
    """Куда сотрудник получает уведомления канала: чат Telegram, пользователь Max, email."""

    __tablename__ = "notification_address"
    __table_args__ = (CheckConstraint("channel_kind IN ('telegram', 'max', 'email')", name="kind"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE"), primary_key=True
    )
    channel_kind: Mapped[str] = mapped_column(String(16), primary_key=True)
    address: Mapped[str] = mapped_column(String(254))
    is_enabled: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class NotificationDelivery(UUIDPrimaryKey, Base):
    """Попытка доставить уведомление в канал: ставится в очередь и повторяется при отказе."""

    __tablename__ = "notification_delivery"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'sent', 'failed')", name="status"),
        CheckConstraint("channel_kind IN ('telegram', 'max', 'email')", name="channel_kind"),
        Index("ix_notification_delivery_due", "status", "next_attempt_at"),
    )

    notification_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("notification.id", ondelete="CASCADE"), index=True
    )
    channel_kind: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="pending")
    attempts: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    next_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Аренда воркера: пока не истекла, другой воркер эту доставку не берёт; упавший — отпускает сам.
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String(300))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
