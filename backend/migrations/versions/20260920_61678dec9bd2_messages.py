"""messages

Переписка сотрудников внутри сервиса: сообщение видят только двое, ссылка на запись
необязательна. Удаление учётной записи уносит её сообщения, удаление взаимодействия
оставляет текст без ссылки.

Revision ID: 61678dec9bd2
Revises: fbc3961ac923
Create Date: 2026-09-20 19:14:13.827673+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "61678dec9bd2"
down_revision: str | Sequence[str] | None = "fbc3961ac923"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "message",
        sa.Column("sender_id", sa.Uuid(), nullable=False),
        sa.Column("recipient_id", sa.Uuid(), nullable=False),
        sa.Column("interaction_id", sa.Uuid(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["interaction_id"],
            ["interaction.id"],
            name=op.f("fk_message_interaction_id_interaction"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["recipient_id"],
            ["app_user.id"],
            name=op.f("fk_message_recipient_id_app_user"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["sender_id"],
            ["app_user.id"],
            name=op.f("fk_message_sender_id_app_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_message")),
    )
    op.create_index(
        "ix_message_dialog", "message", ["sender_id", "recipient_id", "created_at"], unique=False
    )
    op.create_index("ix_message_unread", "message", ["recipient_id", "read_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_message_unread", table_name="message")
    op.drop_index("ix_message_dialog", table_name="message")
    op.drop_table("message")
