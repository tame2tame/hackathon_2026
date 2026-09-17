"""Сохранённые виды: набор фильтров и колонок списка под своим названием."""

import uuid
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, Timestamps, UUIDPrimaryKey

PAGES = ("interactions", "radar", "reports", "rating", "clients")


class SavedView(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "saved_view"
    __table_args__ = (
        CheckConstraint(
            "page IN ('interactions', 'radar', 'reports', 'rating', 'clients')", name="page"
        ),
        UniqueConstraint("user_id", "page", "name"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE"), index=True
    )
    page: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(100))
    # Фильтры и колонки хранятся как есть: их смысл знает страница, а не сервер.
    filters: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    columns: Mapped[list[str]] = mapped_column(JSONB, default=list)
