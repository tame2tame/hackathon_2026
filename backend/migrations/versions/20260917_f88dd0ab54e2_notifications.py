"""notifications

Уведомления сотрудникам, каналы доставки (Telegram, Max, почта), адреса сотрудников в каналах
и журнал доставки. Секреты каналов в базе не хранятся — только имя переменной окружения.

Revision ID: f88dd0ab54e2
Revises: 3102666f4853
Create Date: 2026-09-17 16:14:57.769776+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f88dd0ab54e2"
down_revision: str | Sequence[str] | None = "3102666f4853"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notification_address",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("channel_kind", sa.String(length=16), nullable=False),
        sa.Column("address", sa.String(length=254), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "channel_kind IN ('telegram', 'max', 'email')",
            name=op.f("ck_notification_address_kind"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["app_user.id"],
            name=op.f("fk_notification_address_user_id_app_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "channel_kind", name=op.f("pk_notification_address")),
    )
    op.create_table(
        "notification_channel",
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_mock", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("secret_ref", sa.String(length=120), nullable=True),
        sa.Column("kinds", sa.ARRAY(sa.String(length=40)), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.CheckConstraint(
            "kind IN ('telegram', 'max', 'email')", name=op.f("ck_notification_channel_kind")
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["app_user.id"],
            name=op.f("fk_notification_channel_updated_by_app_user"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("kind", name=op.f("pk_notification_channel")),
    )
    op.create_table(
        "notification",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("interaction_id", sa.Uuid(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("dedupe_key", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint(
            "kind IN ('stalled_interaction', 'stage_changed', 'workflow_changed', 'channel_test')",
            name=op.f("ck_notification_kind"),
        ),
        sa.ForeignKeyConstraint(
            ["interaction_id"],
            ["interaction.id"],
            name=op.f("fk_notification_interaction_id_interaction"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["app_user.id"],
            name=op.f("fk_notification_user_id_app_user"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notification")),
        sa.UniqueConstraint("dedupe_key", name=op.f("uq_notification_dedupe_key")),
    )
    op.create_index(
        "ix_notification_user_created", "notification", ["user_id", "created_at"], unique=False
    )
    op.create_table(
        "notification_delivery",
        sa.Column("notification_id", sa.Uuid(), nullable=False),
        sa.Column("channel_kind", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "next_attempt_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_error", sa.String(length=300), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint(
            "channel_kind IN ('telegram', 'max', 'email')",
            name=op.f("ck_notification_delivery_channel_kind"),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'sent', 'failed')", name=op.f("ck_notification_delivery_status")
        ),
        sa.ForeignKeyConstraint(
            ["notification_id"],
            ["notification.id"],
            name=op.f("fk_notification_delivery_notification_id_notification"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notification_delivery")),
    )
    op.create_index(
        "ix_notification_delivery_due",
        "notification_delivery",
        ["status", "next_attempt_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_delivery_notification_id"),
        "notification_delivery",
        ["notification_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_notification_delivery_notification_id"), table_name="notification_delivery"
    )
    op.drop_index("ix_notification_delivery_due", table_name="notification_delivery")
    op.drop_table("notification_delivery")
    op.drop_index("ix_notification_user_created", table_name="notification")
    op.drop_table("notification")
    op.drop_table("notification_channel")
    op.drop_table("notification_address")
