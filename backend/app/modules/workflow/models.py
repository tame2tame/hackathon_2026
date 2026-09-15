"""Workflow: шаблоны, версии, этапы, правила переходов и нормы длительности этапов."""

import uuid
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, Timestamps, UUIDPrimaryKey


class WorkflowTemplate(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "workflow_template"

    name: Mapped[str] = mapped_column(String(200), unique=True)
    is_default: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WorkflowVersion(UUIDPrimaryKey, Timestamps, Base):
    """Опубликованная версия неизменна по структуре: взаимодействия ссылаются на неё."""

    __tablename__ = "workflow_version"
    __table_args__ = (
        UniqueConstraint("template_id", "version_no"),
        CheckConstraint("status IN ('draft', 'published', 'retired')", name="status"),
    )

    template_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_template.id", ondelete="RESTRICT"), index=True
    )
    version_no: Mapped[int]
    status: Mapped[str] = mapped_column(String(16), default="draft")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    template: Mapped[WorkflowTemplate] = relationship(lazy="raise")
    stages: Mapped[list["Stage"]] = relationship(order_by="Stage.position", lazy="raise")


class Stage(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "stage"
    __table_args__ = (
        UniqueConstraint("version_id", "code"),
        UniqueConstraint("version_id", "position"),
        CheckConstraint("kind IN ('start', 'normal', 'final')", name="kind"),
    )

    version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_version.id", ondelete="RESTRICT"), index=True
    )
    code: Mapped[str] = mapped_column(String(60))
    name: Mapped[str] = mapped_column(String(200))
    position: Mapped[int]
    kind: Mapped[str] = mapped_column(String(16), default="normal")
    bulk_allowed: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    required_document_types: Mapped[list[str]] = mapped_column(
        ARRAY(String(60)), default=list, server_default=text("'{}'")
    )


class StageTransitionRule(UUIDPrimaryKey, Base):
    """Разрешённый переход между этапами одной версии и требования к нему."""

    __tablename__ = "stage_transition_rule"
    __table_args__ = (UniqueConstraint("from_stage_id", "to_stage_id"),)

    version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_version.id", ondelete="RESTRICT"), index=True
    )
    from_stage_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stage.id", ondelete="RESTRICT"))
    to_stage_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stage.id", ondelete="RESTRICT"))
    requires_comment: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    requires_attachment: Mapped[bool] = mapped_column(default=False, server_default=text("false"))

    to_stage: Mapped[Stage] = relationship(foreign_keys=[to_stage_id], lazy="raise")


class StageNorm(UUIDPrimaryKey, Timestamps, Base):
    """Норма длительности этапа в днях. Привязана к коду этапа, поэтому переживает смену версий."""

    __tablename__ = "stage_norm"
    __table_args__ = (
        UniqueConstraint("template_id", "stage_code"),
        CheckConstraint("source IN ('manual', 'suggested')", name="source"),
        CheckConstraint("norm_days > 0", name="norm_days_positive"),
    )

    template_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_template.id", ondelete="RESTRICT")
    )
    stage_code: Mapped[str] = mapped_column(String(60))
    norm_days: Mapped[int]
    source: Mapped[str] = mapped_column(String(16), default="manual")
    suggested_median_days: Mapped[int | None]
    sample_size: Mapped[int | None]
