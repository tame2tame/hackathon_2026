"""integration pull toggle

Входящую синхронизацию источника можно выключить, как и отправку: выключенный источник
не забирается по расписанию, а вручную — по-прежнему.

Revision ID: 8a1aab17784f
Revises: 4e2b7c91d0a3
Create Date: 2026-09-25 16:34:17.821857+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8a1aab17784f"
down_revision: str | Sequence[str] | None = "4e2b7c91d0a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "integration_source",
        sa.Column("pull_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("integration_source", "pull_enabled")
