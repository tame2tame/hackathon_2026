"""program priority

Ручной приоритет курса: рейтинг считается по данным LMS и сайта, но порядок продвижения
руководитель задаёт сам. Ноль — приоритет не задан, такие курсы идут после отмеченных.

Revision ID: c1d4a7f52e08
Revises: b7e2c4d9a1f0
Create Date: 2026-09-18 09:10:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c1d4a7f52e08"
down_revision: str | Sequence[str] | None = "b7e2c4d9a1f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "program",
        sa.Column("priority", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.create_check_constraint("priority_range", "program", sa.text("priority BETWEEN 0 AND 100"))


def downgrade() -> None:
    op.drop_constraint(op.f("ck_program_priority_range"), "program", type_="check")
    op.drop_column("program", "priority")
