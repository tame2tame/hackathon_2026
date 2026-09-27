"""Обучающиеся и преподаватели по записи: ФИО и рабочая почта.

Почта — персональные данные: хранится зашифрованной (ADR-010), а для поиска дублей рядом лежит
её отпечаток — по нему адрес не восстановить, но повторная загрузка того же списка не создаёт
вторую строку на того же человека.
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, LargeBinary, String, text
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.core.db import Base, Timestamps, UUIDPrimaryKey
from app.modules.imports.mapping import normalize

ROLES = ("student", "teacher")
SOURCES = ("manual", "import", "lms")


class Participant(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "participant"
    __table_args__ = (
        CheckConstraint("role IN ('student', 'teacher')", name="role"),
        CheckConstraint("source IN ('manual', 'import', 'lms')", name="source"),
        # Один человек в записи один раз: ключ — отпечаток почты, а без почты — ФИО и роль.
        Index(
            "uq_participant_email",
            "interaction_id",
            "email_fp",
            unique=True,
            postgresql_where="email_fp IS NOT NULL",
        ),
        # Без почты — по ФИО без регистра и знаков: двойной клик не заведёт человека дважды.
        Index(
            "uq_participant_name",
            "interaction_id",
            "role",
            "name_key",
            unique=True,
            postgresql_where=text("email_fp IS NULL AND archived_at IS NULL"),
        ),
        Index("ix_participant_interaction_role", "interaction_id", "role"),
    )

    interaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interaction.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(16))
    full_name: Mapped[str] = mapped_column(String(300))
    # Ключ ФИО для уникального индекса; заполняется сам при каждой записи full_name.
    name_key: Mapped[str] = mapped_column(String(300))
    email_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    email_fp: Mapped[str | None] = mapped_column(String(64))
    external_ref: Mapped[str | None] = mapped_column(String(120))
    source: Mapped[str] = mapped_column(String(16), default="manual")
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL")
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    @validates("full_name")
    def _keep_name_key(self, _key: str, value: str) -> str:
        self.name_key = normalize(value)
        return value
