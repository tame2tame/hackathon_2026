"""Клиенты вне вузов: физические и юридические лица, с которыми работает группа B2C."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, LargeBinary, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, Timestamps, UUIDPrimaryKey

CLIENT_KINDS = ("person", "organization")


class Client(UUIDPrimaryKey, Timestamps, Base):
    """Физическое или юридическое лицо. Email и телефон — ПДн, хранятся зашифрованными."""

    __tablename__ = "client"
    __table_args__ = (
        CheckConstraint("kind IN ('person', 'organization')", name="kind"),
        # Организация узнаётся по ИНН: вторую карточку той же компании завести нельзя.
        Index("uq_client_inn", "inn", unique=True, postgresql_where=text("inn IS NOT NULL")),
    )

    kind: Mapped[str] = mapped_column(String(16))
    # ФИО человека или наименование организации.
    name: Mapped[str] = mapped_column(String(300))
    inn: Mapped[str | None] = mapped_column(String(12))
    city: Mapped[str | None] = mapped_column(String(120))
    email_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    phone_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL"), index=True
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
