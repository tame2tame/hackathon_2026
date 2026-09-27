"""Журнал аудита. Только дописывается: UPDATE и DELETE запрещены триггером."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Identity, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AuditLog(Base):
    __tablename__ = "audit_log"
    # Журнал в админке фильтруют по действию или виду объекта и читают с конца.
    __table_args__ = (
        Index("ix_audit_log_action_occurred_at", "action", "occurred_at"),
        Index("ix_audit_log_entity_kind_occurred_at", "entity_kind", "occurred_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    # Без внешнего ключа: запись аудита не должна мешать архивировать пользователя.
    actor_user_id: Mapped[uuid.UUID | None]
    action: Mapped[str] = mapped_column(String(60))
    entity_kind: Mapped[str] = mapped_column(String(60))
    entity_id: Mapped[uuid.UUID | None]
    before: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    trace_id: Mapped[str | None] = mapped_column(String(32))
