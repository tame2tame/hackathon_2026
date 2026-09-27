"""harden append-only history and audit

История переходов и журнал аудита только дописываются (ADR-005), но построчные триггеры
не ловили TRUNCATE, а режим репликации (`session_replication_role = replica`) отключал их
вовсе. Здесь:

- запрет TRUNCATE отдельным триггером на уровне оператора;
- триггеры в режиме ENABLE ALWAYS — работают и при репликации;
- если на стенде заведена роль приложения `radar_app` (infra/postgres/roles.sql), у неё
  есть права на данные, но на историю и аудит — только чтение и добавление.

Роль владельца таблиц (`radar`) по-прежнему может всё: ею работают миграции, а не приложение.

Revision ID: 5c0d9e3a7b21
Revises: 8a1aab17784f
Create Date: 2026-09-27 12:00:00.000000+00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "5c0d9e3a7b21"
down_revision: str | Sequence[str] | None = "8a1aab17784f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APPEND_ONLY = ("transition", "audit_log")


def upgrade() -> None:
    for table in APPEND_ONLY:
        op.execute(
            f"CREATE TRIGGER {table}_no_truncate BEFORE TRUNCATE ON {table} "
            "FOR EACH STATEMENT EXECUTE FUNCTION forbid_update_delete()"
        )
        op.execute(f"ALTER TABLE {table} ENABLE ALWAYS TRIGGER {table}_append_only")
        op.execute(f"ALTER TABLE {table} ENABLE ALWAYS TRIGGER {table}_no_truncate")

    # Права роли приложения выдаются, только если её завёл скрипт стенда: локально и в CI
    # приложение работает владельцем, и роли нет.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'radar_app') THEN
                GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO radar_app;
                GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO radar_app;
                REVOKE UPDATE, DELETE, TRUNCATE ON transition, audit_log FROM radar_app;
            END IF;
        END
        $$
        """
    )


def downgrade() -> None:
    for table in APPEND_ONLY:
        op.execute(f"ALTER TABLE {table} ENABLE TRIGGER {table}_append_only")
        op.execute(f"DROP TRIGGER IF EXISTS {table}_no_truncate ON {table}")
