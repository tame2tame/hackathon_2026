"""vendor contacts payments client email fingerprint

Данные кейсодержателя: контакты вендоров по продуктам (таблица «Вендоры»), оплаты частных лиц
из платёжной системы и отпечаток почты клиента — по нему повторная оплата находит того же
человека. Откат не удаляет оплаты молча: если они уже загружены, он останавливается.

Revision ID: be016122cefc
Revises: aba0ddc826b7
Create Date: 2026-09-28 12:11:25.967861+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "be016122cefc"
down_revision: str | Sequence[str] | None = "aba0ddc826b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vendor_contact",
        sa.Column("vendor_id", sa.Uuid(), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("name_key", sa.String(length=200), nullable=False),
        sa.Column("email_enc", sa.LargeBinary(), nullable=True),
        sa.Column("phone_enc", sa.LargeBinary(), nullable=True),
        sa.Column(
            "channels",
            sa.ARRAY(sa.String(length=16)),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
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
            "channels <@ ARRAY['email', 'telegram', 'phone']::varchar[]",
            name=op.f("ck_vendor_contact_channels"),
        ),
        sa.ForeignKeyConstraint(
            ["vendor_id"],
            ["vendor.id"],
            name=op.f("fk_vendor_contact_vendor_id_vendor"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vendor_contact")),
    )
    op.create_index(
        "uq_vendor_contact_name",
        "vendor_contact",
        ["vendor_id", "name_key"],
        unique=True,
        postgresql_where=sa.text("archived_at IS NULL"),
    )
    op.create_table(
        "vendor_contact_product",
        sa.Column("contact_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["contact_id"],
            ["vendor_contact.id"],
            name=op.f("fk_vendor_contact_product_contact_id_vendor_contact"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["product.id"],
            name=op.f("fk_vendor_contact_product_product_id_product"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("contact_id", "product_id", name=op.f("pk_vendor_contact_product")),
    )
    op.create_index(
        "ix_vendor_contact_product_product_id",
        "vendor_contact_product",
        ["product_id"],
        unique=False,
    )
    op.create_table(
        "payment",
        sa.Column("order_no", sa.String(length=80), nullable=False),
        sa.Column("interaction_id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("program_id", sa.Uuid(), nullable=False),
        sa.Column("stream_no", sa.Integer(), nullable=True),
        sa.Column("imported_by", sa.Uuid(), nullable=True),
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
            ["client_id"],
            ["client.id"],
            name=op.f("fk_payment_client_id_client"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["imported_by"],
            ["app_user.id"],
            name=op.f("fk_payment_imported_by_app_user"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["interaction_id"],
            ["interaction.id"],
            name=op.f("fk_payment_interaction_id_interaction"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["program_id"],
            ["program.id"],
            name=op.f("fk_payment_program_id_program"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payment")),
        sa.UniqueConstraint("order_no", name=op.f("uq_payment_order_no")),
    )
    op.create_index(op.f("ix_payment_client_id"), "payment", ["client_id"], unique=False)
    op.create_index(op.f("ix_payment_interaction_id"), "payment", ["interaction_id"], unique=False)
    op.add_column("client", sa.Column("email_fp", sa.String(length=64), nullable=True))
    op.create_index(op.f("ix_client_email_fp"), "client", ["email_fp"], unique=False)


def downgrade() -> None:
    op.execute(
        "DO $$ DECLARE hits bigint; BEGIN SELECT count(*) INTO hits FROM payment; "
        "IF hits > 0 THEN RAISE EXCEPTION 'Откат невозможен: загружено % оплат. "
        "Прежняя схема их не хранит.', hits; END IF; END $$"
    )
    op.drop_index(op.f("ix_client_email_fp"), table_name="client")
    op.drop_column("client", "email_fp")
    op.drop_index(op.f("ix_payment_interaction_id"), table_name="payment")
    op.drop_index(op.f("ix_payment_client_id"), table_name="payment")
    op.drop_table("payment")
    op.drop_index("ix_vendor_contact_product_product_id", table_name="vendor_contact_product")
    op.drop_table("vendor_contact_product")
    op.drop_index(
        "uq_vendor_contact_name",
        table_name="vendor_contact",
        postgresql_where=sa.text("archived_at IS NULL"),
    )
    op.drop_table("vendor_contact")
