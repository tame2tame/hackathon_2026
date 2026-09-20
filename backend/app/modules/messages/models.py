"""Переписка сотрудников внутри сервиса: короткие сообщения, при необходимости — о записи."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, Timestamps, UUIDPrimaryKey


class Message(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "message"
    __table_args__ = (
        # Диалог читается по паре собеседников, счётчик непрочитанных — по получателю.
        Index("ix_message_dialog", "sender_id", "recipient_id", "created_at"),
        Index("ix_message_unread", "recipient_id", "read_at"),
    )

    # Порядок сообщений в переписке важен, а `now()` в PostgreSQL постоянен внутри транзакции:
    # два сообщения одной транзакции получили бы одно время. Поэтому время ставит приложение.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_user.id", ondelete="CASCADE"))
    recipient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_user.id", ondelete="CASCADE"))
    # Сообщение может быть о записи: собеседник увидит ссылку, если запись ему доступна.
    interaction_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("interaction.id", ondelete="SET NULL")
    )
    body: Mapped[str] = mapped_column(Text)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
