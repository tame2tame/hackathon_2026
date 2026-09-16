"""Администрирование: правила доступа к данным и настройки приложения."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, Timestamps, UUIDPrimaryKey

EFFECTS = ("allow", "deny")
SCOPE_KINDS = ("university", "direction", "program")


class DataAccessRule(UUIDPrimaryKey, Timestamps, Base):
    """Правило доступа поверх ролей: запрет сильнее разрешения."""

    __tablename__ = "data_access_rule"
    __table_args__ = (
        CheckConstraint("effect IN ('allow', 'deny')", name="effect"),
        CheckConstraint("scope_kind IN ('university', 'direction', 'program')", name="scope_kind"),
        # Правило адресовано либо конкретному сотруднику, либо роли — но не обоим сразу.
        CheckConstraint(
            "(subject_user_id IS NULL) <> (subject_role IS NULL)", name="subject_exactly_one"
        ),
    )

    subject_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE"), index=True
    )
    subject_role: Mapped[str | None] = mapped_column(String(16))
    effect: Mapped[str] = mapped_column(String(8))
    scope_kind: Mapped[str] = mapped_column(String(16))
    scope_id: Mapped[uuid.UUID]
    comment: Mapped[str | None] = mapped_column(Text)


class AppSetting(Base):
    """Настройки, которые меняет администратор: пороги радара, веса рейтинга и прочее."""

    __tablename__ = "app_setting"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL")
    )
