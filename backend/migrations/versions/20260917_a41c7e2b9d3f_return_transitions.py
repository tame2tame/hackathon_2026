"""return transitions in the base workflow

Возврат на шаг назад (уточнение жюри 17.09): у каждого перехода вперёд в опубликованной схеме
базового процесса появляется обратный — с комментарием и без документа. Новые базы получают
эти правила из `ensure_default_workflow`, миграция догоняет уже созданные.

Revision ID: a41c7e2b9d3f
Revises: 3003b18b0343
Create Date: 2026-09-17 18:00:00.000000+00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "a41c7e2b9d3f"
down_revision: str | Sequence[str] | None = "3003b18b0343"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO stage_transition_rule
            (id, version_id, from_stage_id, to_stage_id, requires_comment, requires_attachment)
        SELECT gen_random_uuid(), rule.version_id, rule.to_stage_id, rule.from_stage_id, true, false
        FROM stage_transition_rule AS rule
        JOIN workflow_version AS version ON version.id = rule.version_id
        JOIN workflow_template AS template ON template.id = version.template_id
        JOIN stage AS source ON source.id = rule.from_stage_id
        JOIN stage AS target ON target.id = rule.to_stage_id
        WHERE template.is_default
          AND version.status = 'published'
          AND target.position > source.position
          AND NOT EXISTS (
              SELECT 1 FROM stage_transition_rule AS back
              WHERE back.from_stage_id = rule.to_stage_id
                AND back.to_stage_id = rule.from_stage_id
          )
        """
    )


def downgrade() -> None:
    # До этой миграции в базовом процессе не было ни одного перехода назад.
    op.execute(
        """
        DELETE FROM stage_transition_rule AS rule
        USING workflow_version AS version, workflow_template AS template,
              stage AS source, stage AS target
        WHERE version.id = rule.version_id
          AND template.id = version.template_id
          AND source.id = rule.from_stage_id
          AND target.id = rule.to_stage_id
          AND template.is_default
          AND version.status = 'published'
          AND source.position > target.position
        """
    )
