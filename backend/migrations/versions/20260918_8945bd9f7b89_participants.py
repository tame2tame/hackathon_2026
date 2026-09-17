"""participants

Списки обучающихся и преподавателей по записи. Почта — персональные данные: хранится
зашифрованной, а рядом лежит её отпечаток, по которому загрузка файла находит дубли.

Revision ID: 8945bd9f7b89
Revises: c1d4a7f52e08
Create Date: 2026-09-18 10:40:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8945bd9f7b89"
down_revision: str | Sequence[str] | None = "c1d4a7f52e08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "participant",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("interaction_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("full_name", sa.String(length=300), nullable=False),
        sa.Column("email_enc", sa.LargeBinary(), nullable=True),
        sa.Column("email_fp", sa.String(length=64), nullable=True),
        sa.Column("external_ref", sa.String(length=120), nullable=True),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("role IN ('student', 'teacher')", name=op.f("ck_participant_role")),
        sa.CheckConstraint(
            "source IN ('manual', 'import', 'lms')", name=op.f("ck_participant_source")
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["app_user.id"],
            name=op.f("fk_participant_created_by_app_user"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["interaction_id"],
            ["interaction.id"],
            name=op.f("fk_participant_interaction_id_interaction"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_participant")),
    )
    op.create_index(op.f("ix_participant_interaction_id"), "participant", ["interaction_id"])
    op.create_index("ix_participant_interaction_role", "participant", ["interaction_id", "role"])
    op.create_index(
        "uq_participant_email",
        "participant",
        ["interaction_id", "email_fp"],
        unique=True,
        postgresql_where="email_fp IS NOT NULL",
    )


def downgrade() -> None:
    op.drop_index("uq_participant_email", table_name="participant")
    op.drop_index("ix_participant_interaction_role", table_name="participant")
    op.drop_index(op.f("ix_participant_interaction_id"), table_name="participant")
    op.drop_table("participant")
