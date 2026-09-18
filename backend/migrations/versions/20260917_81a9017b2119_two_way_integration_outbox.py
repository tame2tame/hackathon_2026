"""two-way integration outbox

Исходящий обмен с LMS и CMS: очередь изменённых записей для каждого получателя, признак приёма
изменений у источника и направление запуска в общем журнале обмена.

Revision ID: 81a9017b2119
Revises: f88dd0ab54e2
Create Date: 2026-09-17 16:28:23.582107+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "81a9017b2119"
down_revision: str | Sequence[str] | None = "f88dd0ab54e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "integration_outbox",
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("interaction_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "next_attempt_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_error", sa.String(length=300), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending', 'sent', 'failed')", name=op.f("ck_integration_outbox_status")
        ),
        sa.ForeignKeyConstraint(
            ["interaction_id"],
            ["interaction.id"],
            name=op.f("fk_integration_outbox_interaction_id_interaction"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["integration_source.id"],
            name=op.f("fk_integration_outbox_source_id_integration_source"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_integration_outbox")),
    )
    op.create_index(
        "ix_integration_outbox_due",
        "integration_outbox",
        ["status", "next_attempt_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_integration_outbox_interaction_id"),
        "integration_outbox",
        ["interaction_id"],
        unique=False,
    )
    op.create_index(
        "uq_integration_outbox_pending",
        "integration_outbox",
        ["source_id", "interaction_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.add_column(
        "integration_source",
        sa.Column("push_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    op.add_column(
        "integration_source", sa.Column("last_push_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "sync_run",
        sa.Column("direction", sa.String(length=8), server_default="pull", nullable=False),
    )
    op.create_check_constraint(
        op.f("ck_sync_run_direction"), "sync_run", "direction IN ('pull', 'push')"
    )


def downgrade() -> None:
    # Запуски отправки без очереди и направления теряют смысл: остаются только запуски загрузки.
    op.execute("DELETE FROM sync_run WHERE direction = 'push'")
    op.drop_constraint(op.f("ck_sync_run_direction"), "sync_run", type_="check")
    op.drop_column("sync_run", "direction")
    op.drop_column("integration_source", "last_push_at")
    op.drop_column("integration_source", "push_enabled")
    op.drop_index(
        "uq_integration_outbox_pending",
        table_name="integration_outbox",
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.drop_index(op.f("ix_integration_outbox_interaction_id"), table_name="integration_outbox")
    op.drop_index("ix_integration_outbox_due", table_name="integration_outbox")
    op.drop_table("integration_outbox")
