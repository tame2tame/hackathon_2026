"""one default program product pair

`program_product.is_default` понимали двояко: импорт — как «программа продукта», заявки
с сайта — как «продукт программы», а уникальности не было, и выбор без ORDER BY был случайным.
Теперь флаг — основная пара, одна у программы и одна у продукта.

Если данные уже нарушают правило, миграция останавливается и называет число пар: какую
оставить основной, решает администратор.

Revision ID: aba0ddc826b7
Revises: d55432f48d23
Create Date: 2026-09-27 01:32:05.556852+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "aba0ddc826b7"
down_revision: str | Sequence[str] | None = "d55432f48d23"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        DECLARE hits bigint;
        BEGIN
            SELECT count(*) INTO hits FROM (
                SELECT program_id FROM program_product WHERE is_default
                GROUP BY program_id HAVING count(*) > 1
                UNION ALL
                SELECT product_id FROM program_product WHERE is_default
                GROUP BY product_id HAVING count(*) > 1
            ) AS doubles;
            IF hits > 0 THEN
                RAISE EXCEPTION 'Основная пара программа-продукт задана дважды у % программ '
                    'или продуктов. Оставьте одну и повторите миграцию.', hits;
            END IF;
        END $$
        """
    )
    op.create_index(
        "uq_program_product_default_product",
        "program_product",
        ["product_id"],
        unique=True,
        postgresql_where=sa.text("is_default"),
    )
    op.create_index(
        "uq_program_product_default_program",
        "program_product",
        ["program_id"],
        unique=True,
        postgresql_where=sa.text("is_default"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_program_product_default_program",
        table_name="program_product",
        postgresql_where=sa.text("is_default"),
    )
    op.drop_index(
        "uq_program_product_default_product",
        table_name="program_product",
        postgresql_where=sa.text("is_default"),
    )
