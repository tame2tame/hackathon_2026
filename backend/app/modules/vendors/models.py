"""Контакты вендоров: к кому идти по продукту, когда вуз или слушатель просит помощи.

Кейсодержатель ведёт их таблицей «Компания — Продукт — ФИО — Телефон — Почта — Способ связи»:
у каждого продукта свой человек, а один человек может отвечать за несколько продуктов вендора.
Почта и телефон — персональные данные, хранятся зашифрованными, как у контактов вуза (ADR-010).
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    LargeBinary,
    String,
    Table,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.core.db import Base, Timestamps, UUIDPrimaryKey
from app.modules.imports.mapping import normalize

# Способы связи из таблицы кейсодержателя: «Почта», «Чат в ТГ» и их сочетания.
CHANNELS = ("email", "telegram", "phone")

vendor_contact_product = Table(
    "vendor_contact_product",
    Base.metadata,
    Column("contact_id", ForeignKey("vendor_contact.id", ondelete="CASCADE"), primary_key=True),
    Column("product_id", ForeignKey("product.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_vendor_contact_product_product_id", "product_id"),
)


class VendorContact(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "vendor_contact"
    __table_args__ = (
        # Один человек у вендора один раз: повторная загрузка таблицы находит его по ФИО.
        Index(
            "uq_vendor_contact_name",
            "vendor_id",
            "name_key",
            unique=True,
            postgresql_where=text("archived_at IS NULL"),
        ),
        CheckConstraint(
            "channels <@ ARRAY['email', 'telegram', 'phone']::varchar[]", name="channels"
        ),
    )

    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendor.id", ondelete="RESTRICT"))
    full_name: Mapped[str] = mapped_column(String(200))
    name_key: Mapped[str] = mapped_column(String(200))
    email_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    phone_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    channels: Mapped[list[str]] = mapped_column(
        ARRAY(String(16)), default=list, server_default=text("'{}'")
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    @validates("full_name")
    def _keep_name_key(self, _key: str, value: str) -> str:
        self.name_key = normalize(value)
        return value
