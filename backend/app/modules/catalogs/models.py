"""Каталоги: вузы, направления, программы, вендоры, продукты, контакты, команды, пользователи."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    LargeBinary,
    String,
    Table,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, Timestamps, UUIDPrimaryKey


class University(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "university"

    name: Mapped[str] = mapped_column(String(300), unique=True)
    short_name: Mapped[str] = mapped_column(String(60))
    region: Mapped[str] = mapped_column(String(120))
    city: Mapped[str | None] = mapped_column(String(120))
    is_priority2030: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Direction(UUIDPrimaryKey, Timestamps, Base):
    """ИТ-направление обучения, например DevOps."""

    __tablename__ = "direction"

    code: Mapped[str] = mapped_column(String(60), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    # Каталоги не удаляются: на них ссылается история, поэтому запись архивируется.
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Program(UUIDPrimaryKey, Timestamps, Base):
    """ИТ-программа: методические материалы и практика по направлению."""

    __tablename__ = "program"
    __table_args__ = (UniqueConstraint("direction_id", "name"),)

    direction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("direction.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(300))
    lms_course_ref: Mapped[str | None] = mapped_column(String(120))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    direction: Mapped[Direction] = relationship(lazy="raise")


class Vendor(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "vendor"

    name: Mapped[str] = mapped_column(String(200), unique=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


product_direction = Table(
    "product_direction",
    Base.metadata,
    Column("product_id", ForeignKey("product.id", ondelete="CASCADE"), primary_key=True),
    Column("direction_id", ForeignKey("direction.id", ondelete="RESTRICT"), primary_key=True),
)


class Product(UUIDPrimaryKey, Timestamps, Base):
    """ИТ-продукт — ПО вендора, которое передаётся вузу."""

    __tablename__ = "product"
    __table_args__ = (UniqueConstraint("vendor_id", "name"),)

    vendor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vendor.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    vendor: Mapped[Vendor] = relationship(lazy="raise")


class ProgramProduct(Base):
    """Продукты программы; is_default выбирает программу по продукту при импорте."""

    __tablename__ = "program_product"

    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("program.id", ondelete="CASCADE"), primary_key=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), primary_key=True
    )
    is_default: Mapped[bool] = mapped_column(default=False, server_default=text("false"))


class ContactPerson(UUIDPrimaryKey, Timestamps, Base):
    """Ответственный со стороны вуза. Email и телефон — ПДн, хранятся зашифрованными."""

    __tablename__ = "contact_person"

    university_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("university.id", ondelete="RESTRICT"), index=True
    )
    full_name: Mapped[str] = mapped_column(String(200))
    position: Mapped[str | None] = mapped_column(String(200))
    email_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    phone_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Team(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "team"

    name: Mapped[str] = mapped_column(String(120), unique=True)
    # use_alter разрывает циклическую зависимость team ↔ app_user при создании таблиц.
    manager_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL", use_alter=True)
    )


class AppUser(UUIDPrimaryKey, Timestamps, Base):
    """Сотрудник ИТ Школы. Роль приходит из Keycloak, команда хранится здесь."""

    __tablename__ = "app_user"
    __table_args__ = (CheckConstraint("role IN ('kam', 'manager', 'admin')", name="role"),)

    keycloak_sub: Mapped[str | None] = mapped_column(String(64), unique=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    full_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(16))
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("team.id", ondelete="SET NULL"), index=True
    )
    is_active: Mapped[bool] = mapped_column(default=True, server_default=text("true"))

    team: Mapped[Team | None] = relationship(foreign_keys=[team_id], lazy="raise")
