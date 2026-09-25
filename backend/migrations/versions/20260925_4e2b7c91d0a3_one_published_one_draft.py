"""one published and one draft version per process

У процесса одна действующая схема и один черновик. Без этих индексов две почти одновременные
публикации оставляли две «действующие» версии, и записи второй больше никуда не переносились.

Если в базе уже есть процесс с двумя опубликованными версиями или двумя черновиками, миграция
останавливается и называет его: какую версию оставить — решает человек, а не миграция.

Revision ID: 4e2b7c91d0a3
Revises: 61678dec9bd2
Create Date: 2026-09-25 18:30:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "4e2b7c91d0a3"
down_revision: str | Sequence[str] | None = "61678dec9bd2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _refuse_duplicates(status: str) -> None:
    rows = (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT t.name, count(*) FROM workflow_version v "
                "JOIN workflow_template t ON t.id = v.template_id "
                "WHERE v.status = :status GROUP BY t.name HAVING count(*) > 1"
            ),
            {"status": status},
        )
        .all()
    )
    if rows:
        names = ", ".join(f"«{name}» ({count})" for name, count in rows)
        raise RuntimeError(
            f"У процессов несколько версий в состоянии {status}: {names}. "
            "Оставьте одну (остальные переведите в retired) и повторите миграцию."
        )


def upgrade() -> None:
    _refuse_duplicates("published")
    _refuse_duplicates("draft")
    op.create_index(
        "uq_workflow_version_published",
        "workflow_version",
        ["template_id"],
        unique=True,
        postgresql_where=sa.text("status = 'published'"),
    )
    op.create_index(
        "uq_workflow_version_draft",
        "workflow_version",
        ["template_id"],
        unique=True,
        postgresql_where=sa.text("status = 'draft'"),
    )


def downgrade() -> None:
    op.drop_index("uq_workflow_version_draft", table_name="workflow_version")
    op.drop_index("uq_workflow_version_published", table_name="workflow_version")
