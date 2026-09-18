#!/bin/sh
# Проверка восстановления: дамп разворачивается во временную базу и проверяется на целостность.
# Бэкап без проверки восстановления — это надежда, а не резервная копия.
# Запуск: sh infra/backup/restore-check.sh [файл дампа]
set -eu

: "${PGHOST:=postgres}"
: "${PGUSER:=radar}"
: "${BACKUP_DIR:=/backups}"
CHECK_DB="radar_restore_check"

FILE="${1:-$(find "$BACKUP_DIR" -name 'radar-*.dump' -type f | sort | tail -1)}"
if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
    echo "Не найден дамп для проверки в $BACKUP_DIR" >&2
    exit 1
fi
echo "Проверяем $FILE"

dropdb --host="$PGHOST" --username="$PGUSER" --if-exists "$CHECK_DB"
createdb --host="$PGHOST" --username="$PGUSER" "$CHECK_DB"
pg_restore --host="$PGHOST" --username="$PGUSER" --dbname="$CHECK_DB" --no-owner "$FILE"

TABLES=$(psql --host="$PGHOST" --username="$PGUSER" --dbname="$CHECK_DB" -Atc \
    "select count(*) from pg_tables where schemaname='public'")
INTERACTIONS=$(psql --host="$PGHOST" --username="$PGUSER" --dbname="$CHECK_DB" -Atc \
    "select count(*) from interaction")
TRANSITIONS=$(psql --host="$PGHOST" --username="$PGUSER" --dbname="$CHECK_DB" -Atc \
    "select count(*) from transition")

echo "Таблиц: $TABLES, взаимодействий: $INTERACTIONS, переходов: $TRANSITIONS"
dropdb --host="$PGHOST" --username="$PGUSER" "$CHECK_DB"

if [ "$TABLES" -lt 25 ] || [ "$INTERACTIONS" -lt 1 ]; then
    echo "Восстановление неполное: проверьте дамп" >&2
    exit 1
fi
echo "Восстановление проверено"
