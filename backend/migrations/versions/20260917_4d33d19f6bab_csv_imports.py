"""csv imports

CSV на входе и на выходе: у загрузки сохраняются кодировка и разделитель, с которыми прочитан файл,
профиль соответствия колонок и задание на отчёт допускают формат csv.

Revision ID: 4d33d19f6bab
Revises: 81a9017b2119
Create Date: 2026-09-17 16:45:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "4d33d19f6bab"
down_revision: str | Sequence[str] | None = "81a9017b2119"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("import_batch", sa.Column("encoding", sa.String(length=20), nullable=True))
    op.add_column("import_batch", sa.Column("delimiter", sa.String(length=1), nullable=True))
    op.drop_constraint(op.f("ck_import_profile_file_kind"), "import_profile", type_="check")
    op.create_check_constraint(
        op.f("ck_import_profile_file_kind"), "import_profile", "file_kind IN ('xls', 'xlsx', 'csv')"
    )
    op.drop_constraint(op.f("ck_report_job_format"), "report_job", type_="check")
    op.create_check_constraint(
        op.f("ck_report_job_format"),
        "report_job",
        "format IN ('xlsx', 'xls', 'csv', 'pdf', 'json')",
    )


def downgrade() -> None:
    blocking = (
        op.get_bind()
        .execute(sa.text("SELECT count(*) FROM import_profile WHERE file_kind = 'csv'"))
        .scalar_one()
    )
    if blocking:
        raise RuntimeError(f"Откат невозможен: {blocking} профилей импорта для CSV.")
    # Задания на CSV-отчёты — только журнал: без формата csv прежняя схема их не примет.
    op.execute("DELETE FROM report_job WHERE format = 'csv'")
    op.drop_constraint(op.f("ck_report_job_format"), "report_job", type_="check")
    op.create_check_constraint(
        op.f("ck_report_job_format"), "report_job", "format IN ('xlsx', 'xls', 'pdf', 'json')"
    )
    op.drop_constraint(op.f("ck_import_profile_file_kind"), "import_profile", type_="check")
    op.create_check_constraint(
        op.f("ck_import_profile_file_kind"), "import_profile", "file_kind IN ('xls', 'xlsx')"
    )
    op.drop_column("import_batch", "delimiter")
    op.drop_column("import_batch", "encoding")
