"""review indexes

Недостающие индексы под реальные запросы: курсор выгрузки обмена (updated_at, id), перенос
записей на новую схему (workflow_version_id), эскалация и срок хранения (last_activity_at),
заявки сайта по записи и по статусу сопоставления, журнал аудита по действию и виду объекта.

Лишние — девять индексов по первому столбцу уникальных ограничений: ограничение уже само
индекс с тем же первым столбцом, а второй только замедлял запись.

Revision ID: d55432f48d23
Revises: 7d4e1f0a9b62
Create Date: 2026-09-27 01:28:23.438594+00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d55432f48d23"
down_revision: str | Sequence[str] | None = "7d4e1f0a9b62"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_audit_log_action_occurred_at", "audit_log", ["action", "occurred_at"], unique=False
    )
    op.create_index(
        "ix_audit_log_entity_kind_occurred_at",
        "audit_log",
        ["entity_kind", "occurred_at"],
        unique=False,
    )
    op.drop_index(op.f("ix_contract_university_id"), table_name="contract")
    op.drop_index(op.f("ix_import_row_batch_id"), table_name="import_row")
    op.create_index(
        "ix_interaction_last_activity_at", "interaction", ["last_activity_at"], unique=False
    )
    op.create_index("ix_interaction_updated_at", "interaction", ["updated_at", "id"], unique=False)
    op.create_index(
        "ix_interaction_workflow_version_id", "interaction", ["workflow_version_id"], unique=False
    )
    op.drop_index(op.f("ix_participant_interaction_id"), table_name="participant")
    op.drop_index(op.f("ix_product_vendor_id"), table_name="product")
    op.drop_index(op.f("ix_program_direction_id"), table_name="program")
    op.drop_index(op.f("ix_program_metric_university_id"), table_name="program_metric")
    op.drop_index(op.f("ix_saved_view_user_id"), table_name="saved_view")
    op.create_index(
        "ix_site_application_interaction_id", "site_application", ["interaction_id"], unique=False
    )
    op.create_index(
        "ix_site_application_match_status", "site_application", ["match_status"], unique=False
    )
    op.drop_index(op.f("ix_stage_version_id"), table_name="stage")
    op.drop_index(op.f("ix_workflow_version_template_id"), table_name="workflow_version")


def downgrade() -> None:
    op.create_index(
        op.f("ix_workflow_version_template_id"), "workflow_version", ["template_id"], unique=False
    )
    op.create_index(op.f("ix_stage_version_id"), "stage", ["version_id"], unique=False)
    op.drop_index("ix_site_application_match_status", table_name="site_application")
    op.drop_index("ix_site_application_interaction_id", table_name="site_application")
    op.create_index(op.f("ix_saved_view_user_id"), "saved_view", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_program_metric_university_id"), "program_metric", ["university_id"], unique=False
    )
    op.create_index(op.f("ix_program_direction_id"), "program", ["direction_id"], unique=False)
    op.create_index(op.f("ix_product_vendor_id"), "product", ["vendor_id"], unique=False)
    op.create_index(
        op.f("ix_participant_interaction_id"), "participant", ["interaction_id"], unique=False
    )
    op.drop_index("ix_interaction_workflow_version_id", table_name="interaction")
    op.drop_index("ix_interaction_updated_at", table_name="interaction")
    op.drop_index("ix_interaction_last_activity_at", table_name="interaction")
    op.create_index(op.f("ix_import_row_batch_id"), "import_row", ["batch_id"], unique=False)
    op.create_index(op.f("ix_contract_university_id"), "contract", ["university_id"], unique=False)
    op.drop_index("ix_audit_log_entity_kind_occurred_at", table_name="audit_log")
    op.drop_index("ix_audit_log_action_occurred_at", table_name="audit_log")
