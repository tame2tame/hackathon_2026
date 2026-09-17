"""queue leases

Очереди исходящего обмена и доставки уведомлений захватываются арендой, а не блокировкой
на время сетевого вызова: `locked_until` у обеих очередей и счётчик изменений `change_seq`
у outbox, чтобы изменение во время отправки не потерялось.

Revision ID: b7e2c4d9a1f0
Revises: 4d33d19f6bab
Create Date: 2026-09-17 19:30:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7e2c4d9a1f0"
down_revision: str | Sequence[str] | None = "4d33d19f6bab"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "integration_outbox",
        sa.Column("change_seq", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
    )
    op.add_column(
        "integration_outbox", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "notification_delivery",
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("notification_delivery", "locked_until")
    op.drop_column("integration_outbox", "locked_until")
    op.drop_column("integration_outbox", "change_seq")
