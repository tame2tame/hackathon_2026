"""Взаимодействия (контрагент × программа × продукт), договоры, история, заметки, вложения."""

import uuid
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, Timestamps, UUIDPrimaryKey
from app.modules.catalogs.models import AppUser, CounterpartyGroup, Product, Program, University
from app.modules.clients.models import Client
from app.modules.workflow.models import Stage, WorkflowVersion


class Contract(UUIDPrimaryKey, Timestamps, Base):
    """Договор с вузом; один договор может покрывать несколько взаимодействий."""

    __tablename__ = "contract"
    __table_args__ = (UniqueConstraint("university_id", "number"),)

    university_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("university.id", ondelete="RESTRICT")
    )
    number: Mapped[str] = mapped_column(String(60))
    signed_at: Mapped[date | None]
    license_signed_at: Mapped[date | None]
    license_valid_until: Mapped[date | None]
    license_term_years: Mapped[int | None]
    transfer_status: Mapped[str | None] = mapped_column(String(120))


@dataclass(frozen=True, slots=True)
class Counterparty:
    kind: str
    id: uuid.UUID
    name: str
    short_name: str


class Interaction(UUIDPrimaryKey, Timestamps, Base):
    """Центральная запись (ADR-001, ADR-015): контрагент группы по ИТ-программе и продукту.

    Контрагент — ровно один: вуз или клиент. Продукт необязателен: программы бывают
    продуктонезависимыми.
    """

    __tablename__ = "interaction"
    __table_args__ = (
        # Одна активная связка на контрагента, программу и продукт; пустой продукт — тоже значение.
        # Отменённые записи не мешают завести связку заново.
        Index(
            "uq_interaction_active_university",
            "university_id",
            "program_id",
            "product_id",
            unique=True,
            postgresql_where=text("status <> 'cancelled' AND university_id IS NOT NULL"),
            postgresql_nulls_not_distinct=True,
        ),
        Index(
            "uq_interaction_active_client",
            "client_id",
            "program_id",
            "product_id",
            unique=True,
            postgresql_where=text("status <> 'cancelled' AND client_id IS NOT NULL"),
            postgresql_nulls_not_distinct=True,
        ),
        Index("ix_interaction_owner_status", "owner_user_id", "status"),
        Index("ix_interaction_stage_entered", "current_stage_id", "stage_entered_at"),
        # Выгрузка обмена идёт по курсору (updated_at, id), перенос на новую схему — по версии,
        # эскалация и срок хранения — по последней активности.
        Index("ix_interaction_updated_at", "updated_at", "id"),
        Index("ix_interaction_workflow_version_id", "workflow_version_id"),
        Index("ix_interaction_last_activity_at", "last_activity_at"),
        CheckConstraint("status IN ('active', 'paused', 'completed', 'cancelled')", name="status"),
        CheckConstraint("source IN ('manual', 'import', 'site', 'lms', 'demo')", name="source"),
        CheckConstraint(
            "(university_id IS NULL) <> (client_id IS NULL)", name="counterparty_exactly_one"
        ),
    )

    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("counterparty_group.id", ondelete="RESTRICT"), index=True
    )
    university_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("university.id", ondelete="RESTRICT"), index=True
    )
    client_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("client.id", ondelete="RESTRICT"), index=True
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("program.id", ondelete="RESTRICT"), index=True
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("product.id", ondelete="RESTRICT"), index=True
    )
    contract_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("contract.id", ondelete="RESTRICT")
    )
    workflow_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_version.id", ondelete="RESTRICT")
    )
    current_stage_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stage.id", ondelete="RESTRICT"))
    stage_entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    owner_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_user.id", ondelete="RESTRICT"))
    status: Mapped[str] = mapped_column(String(16), default="active")
    source: Mapped[str] = mapped_column(String(16), default="manual")
    # Версия записи для защиты от параллельных изменений (ADR-009).
    version: Mapped[int] = mapped_column(default=1, server_default=text("1"))
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    group: Mapped[CounterpartyGroup] = relationship(lazy="raise")
    university: Mapped[University | None] = relationship(lazy="raise")
    client: Mapped[Client | None] = relationship(lazy="raise")
    program: Mapped[Program] = relationship(lazy="raise")
    product: Mapped[Product | None] = relationship(lazy="raise")
    contract: Mapped[Contract | None] = relationship(lazy="raise")
    workflow_version: Mapped[WorkflowVersion] = relationship(lazy="raise")
    current_stage: Mapped[Stage] = relationship(lazy="raise")
    owner: Mapped[AppUser] = relationship(lazy="raise")

    @property
    def counterparty(self) -> Counterparty:
        """Вуз или клиент; связь должна быть загружена вместе с записью."""
        if self.university_id is not None and self.university is not None:
            university = self.university
            return Counterparty("university", university.id, university.name, university.short_name)
        if self.client is None:
            raise ValueError("У взаимодействия нет контрагента")
        return Counterparty(self.client.kind, self.client.id, self.client.name, self.client.name)


class InteractionContact(Base):
    __tablename__ = "interaction_contact"

    interaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interaction.id", ondelete="CASCADE"), primary_key=True
    )
    contact_person_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contact_person.id", ondelete="RESTRICT"), primary_key=True
    )
    role: Mapped[str | None] = mapped_column(String(120))


class Transition(UUIDPrimaryKey, Base):
    """Запись истории. Только дописывается: UPDATE и DELETE запрещены триггером (ADR-005)."""

    __tablename__ = "transition"
    __table_args__ = (
        Index("ix_transition_interaction_occurred", "interaction_id", "occurred_at"),
        CheckConstraint(
            "source IN ('manual', 'bulk', 'import', 'integration', 'migration')", name="source"
        ),
    )

    interaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interaction.id", ondelete="RESTRICT")
    )
    from_stage_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("stage.id", ondelete="RESTRICT")
    )
    to_stage_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stage.id", ondelete="RESTRICT"))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT")
    )
    comment: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(16), default="manual")

    from_stage: Mapped[Stage | None] = relationship(foreign_keys=[from_stage_id], lazy="raise")
    to_stage: Mapped[Stage] = relationship(foreign_keys=[to_stage_id], lazy="raise")
    actor: Mapped[AppUser | None] = relationship(lazy="raise")


class InteractionNote(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "interaction_note"

    interaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interaction.id", ondelete="RESTRICT"), index=True
    )
    author_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT")
    )
    text: Mapped[str] = mapped_column(Text)


class Attachment(UUIDPrimaryKey, Base):
    __tablename__ = "attachment"

    interaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interaction.id", ondelete="RESTRICT"), index=True
    )
    transition_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("transition.id", ondelete="RESTRICT")
    )
    stage_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stage.id", ondelete="RESTRICT"))
    document_type: Mapped[str | None] = mapped_column(String(60))
    file_name: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    sha256: Mapped[str] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(String(300))
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_user.id", ondelete="RESTRICT"))
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AssignmentChange(UUIDPrimaryKey, Base):
    """Смена ответственного КАМа — для истории карточки и аудита."""

    __tablename__ = "assignment_change"

    interaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interaction.id", ondelete="RESTRICT"), index=True
    )
    from_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="RESTRICT")
    )
    to_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_user.id", ondelete="RESTRICT"))
    changed_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_user.id", ondelete="RESTRICT"))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reason: Mapped[str | None] = mapped_column(Text)
