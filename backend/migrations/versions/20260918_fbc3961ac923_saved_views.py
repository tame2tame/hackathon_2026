"""saved views

Сохранённый вид — фильтры и колонки списка под своим названием. Свои у каждого пользователя:
удаление учётной записи уносит и её виды.

Revision ID: fbc3961ac923
Revises: 8945bd9f7b89
Create Date: 2026-09-18 21:55:08.912191+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "fbc3961ac923"
down_revision: str | Sequence[str] | None = "8945bd9f7b89"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "saved_view",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("page", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("filters", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("columns", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.CheckConstraint(
            "page IN ('interactions', 'radar', 'reports', 'rating', 'clients')",
            name=op.f("ck_saved_view_page"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["app_user.id"],
            name=op.f("fk_saved_view_user_id_app_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_saved_view")),
        sa.UniqueConstraint(
            "user_id", "page", "name", name=op.f("uq_saved_view_user_id_page_name")
        ),
    )
    op.create_index(op.f("ix_saved_view_user_id"), "saved_view", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_saved_view_user_id"), table_name="saved_view")
    op.drop_table("saved_view")
