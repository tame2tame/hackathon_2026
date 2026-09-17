"""counterparty groups and clients

Группы контрагентов со своим процессом (B2B — вузы, B2C — частные лица) и клиенты вне вузов.
Взаимодействие получает группу и клиента; вуз и продукт становятся необязательными, контрагент —
ровно один. Существующие записи попадают в группу «Вузы (B2B)» с базовым процессом.

Revision ID: 3102666f4853
Revises: a41c7e2b9d3f
Create Date: 2026-09-17 15:53:39.791747+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "3102666f4853"
down_revision: str | Sequence[str] | None = "a41c7e2b9d3f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "counterparty_group",
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("workflow_template_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), server_default=sa.text("0"), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["workflow_template_id"],
            ["workflow_template.id"],
            name=op.f("fk_counterparty_group_workflow_template_id_workflow_template"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_counterparty_group")),
        sa.UniqueConstraint("code", name=op.f("uq_counterparty_group_code")),
        sa.UniqueConstraint("name", name=op.f("uq_counterparty_group_name")),
    )
    op.create_index(
        op.f("ix_counterparty_group_workflow_template_id"),
        "counterparty_group",
        ["workflow_template_id"],
        unique=False,
    )
    op.create_table(
        "client",
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("inn", sa.String(length=12), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("email_enc", sa.LargeBinary(), nullable=True),
        sa.Column("phone_enc", sa.LargeBinary(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
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
        sa.CheckConstraint("kind IN ('person', 'organization')", name=op.f("ck_client_kind")),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["app_user.id"],
            name=op.f("fk_client_created_by_app_user"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_client")),
    )
    op.create_index(op.f("ix_client_created_by"), "client", ["created_by"], unique=False)
    op.create_index(
        "uq_client_inn", "client", ["inn"], unique=True, postgresql_where=sa.text("inn IS NOT NULL")
    )

    op.add_column("interaction", sa.Column("group_id", sa.Uuid(), nullable=True))
    op.add_column("interaction", sa.Column("client_id", sa.Uuid(), nullable=True))
    # Уже созданные записи — работа с вузами по базовому процессу. Группа появляется, только если
    # базовый процесс уже заведён; в пустой базе группы создаёт загрузка демо-данных.
    op.execute(
        """
        INSERT INTO counterparty_group (id, code, name, description, workflow_template_id, position)
        SELECT gen_random_uuid(), 'universities', 'Вузы (B2B)',
               'Работа с вузами по ИТ-программам и продуктам', template.id, 1
        FROM workflow_template AS template
        WHERE template.is_default
        ORDER BY template.created_at
        LIMIT 1
        """
    )
    op.execute(
        """
        UPDATE interaction
        SET group_id = (SELECT id FROM counterparty_group WHERE code = 'universities')
        """
    )
    op.alter_column("interaction", "group_id", existing_type=sa.Uuid(), nullable=False)
    op.alter_column("interaction", "university_id", existing_type=sa.UUID(), nullable=True)
    op.alter_column("interaction", "product_id", existing_type=sa.UUID(), nullable=True)
    op.drop_index(
        op.f("uq_interaction_active_triple"),
        table_name="interaction",
        postgresql_where="((status)::text <> 'cancelled'::text)",
    )
    op.create_index(op.f("ix_interaction_client_id"), "interaction", ["client_id"], unique=False)
    op.create_index(op.f("ix_interaction_group_id"), "interaction", ["group_id"], unique=False)
    op.create_index(
        "uq_interaction_active_client",
        "interaction",
        ["client_id", "program_id", "product_id"],
        unique=True,
        postgresql_where=sa.text("status <> 'cancelled' AND client_id IS NOT NULL"),
        postgresql_nulls_not_distinct=True,
    )
    op.create_index(
        "uq_interaction_active_university",
        "interaction",
        ["university_id", "program_id", "product_id"],
        unique=True,
        postgresql_where=sa.text("status <> 'cancelled' AND university_id IS NOT NULL"),
        postgresql_nulls_not_distinct=True,
    )
    op.create_foreign_key(
        op.f("fk_interaction_client_id_client"),
        "interaction",
        "client",
        ["client_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        op.f("fk_interaction_group_id_counterparty_group"),
        "interaction",
        "counterparty_group",
        ["group_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        op.f("ck_interaction_counterparty_exactly_one"),
        "interaction",
        "(university_id IS NULL) <> (client_id IS NULL)",
    )
    op.drop_constraint(op.f("ck_data_access_rule_scope_kind"), "data_access_rule", type_="check")
    op.create_check_constraint(
        op.f("ck_data_access_rule_scope_kind"),
        "data_access_rule",
        "scope_kind IN ('university', 'direction', 'program', 'group')",
    )


def downgrade() -> None:
    bind = op.get_bind()
    blocking = bind.execute(
        sa.text(
            "SELECT count(*) FROM interaction WHERE client_id IS NOT NULL OR product_id IS NULL"
        )
    ).scalar_one()
    if blocking:
        # История переходов только дописывается, поэтому такие записи не удалить молча.
        raise RuntimeError(
            f"Откат невозможен: {blocking} взаимодействий с клиентом вне вузов или без продукта. "
            "Прежняя схема не умеет их хранить."
        )
    group_rules = bind.execute(
        sa.text("SELECT count(*) FROM data_access_rule WHERE scope_kind = 'group'")
    ).scalar_one()
    if group_rules:
        raise RuntimeError(
            f"Откат невозможен: {group_rules} правил доступа по группе. Удалите их в админке."
        )

    op.drop_constraint(op.f("ck_data_access_rule_scope_kind"), "data_access_rule", type_="check")
    op.create_check_constraint(
        op.f("ck_data_access_rule_scope_kind"),
        "data_access_rule",
        "scope_kind IN ('university', 'direction', 'program')",
    )
    op.drop_constraint(
        op.f("ck_interaction_counterparty_exactly_one"), "interaction", type_="check"
    )
    op.drop_constraint(
        op.f("fk_interaction_group_id_counterparty_group"), "interaction", type_="foreignkey"
    )
    op.drop_constraint(op.f("fk_interaction_client_id_client"), "interaction", type_="foreignkey")
    op.drop_index("uq_interaction_active_university", table_name="interaction")
    op.drop_index("uq_interaction_active_client", table_name="interaction")
    op.drop_index(op.f("ix_interaction_group_id"), table_name="interaction")
    op.drop_index(op.f("ix_interaction_client_id"), table_name="interaction")
    op.create_index(
        op.f("uq_interaction_active_triple"),
        "interaction",
        ["university_id", "program_id", "product_id"],
        unique=True,
        postgresql_where=sa.text("status <> 'cancelled'"),
    )
    op.alter_column("interaction", "product_id", existing_type=sa.UUID(), nullable=False)
    op.alter_column("interaction", "university_id", existing_type=sa.UUID(), nullable=False)
    op.drop_column("interaction", "client_id")
    op.drop_column("interaction", "group_id")
    op.drop_index("uq_client_inn", table_name="client")
    op.drop_index(op.f("ix_client_created_by"), table_name="client")
    op.drop_table("client")
    op.drop_index(
        op.f("ix_counterparty_group_workflow_template_id"), table_name="counterparty_group"
    )
    op.drop_table("counterparty_group")
