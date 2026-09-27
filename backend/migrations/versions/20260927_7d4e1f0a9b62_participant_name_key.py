"""participant name key

Участника без почты от повторного добавления защищала только проверка в коде, и двойной клик
её обходил. Теперь у строки есть ключ ФИО (без регистра, пробелов и знаков — как `normalize`
в импорте), а частичный уникальный индекс не даёт завести двух одинаковых людей без почты
в одной роли одной записи.

Если дубли уже успели появиться, данные не удаляются: ключ у лишних строк получает суффикс
с их id, чтобы индекс создался, а разобрать их можно в карточке записи.

Revision ID: 7d4e1f0a9b62
Revises: 5c0d9e3a7b21
Create Date: 2026-09-27 14:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7d4e1f0a9b62"
down_revision: str | Sequence[str] | None = "5c0d9e3a7b21"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("participant", sa.Column("name_key", sa.String(length=300), nullable=True))
    op.execute(
        "UPDATE participant "
        "SET name_key = regexp_replace(lower(full_name), '[^[:alnum:]]', '', 'g')"
    )
    op.execute(
        """
        UPDATE participant p
        SET name_key = p.name_key || ':' || p.id
        FROM (
            SELECT id, row_number() OVER (
                PARTITION BY interaction_id, role, name_key ORDER BY created_at, id
            ) AS n
            FROM participant
            WHERE email_fp IS NULL AND archived_at IS NULL
        ) d
        WHERE d.id = p.id AND d.n > 1
        """
    )
    op.alter_column("participant", "name_key", nullable=False)
    op.create_index(
        "uq_participant_name",
        "participant",
        ["interaction_id", "role", "name_key"],
        unique=True,
        postgresql_where=sa.text("email_fp IS NULL AND archived_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_participant_name", table_name="participant")
    op.drop_column("participant", "name_key")
