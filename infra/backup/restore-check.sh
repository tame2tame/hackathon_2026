#!/bin/sh
# Проверка восстановления: свежие дампы обеих баз разворачиваются во временные базы
# и сверяются с рабочими. Бэкап без проверки восстановления — это надежда, а не резервная копия.
# Запуск: sh infra/backup/restore-check.sh [дамп radar] [дамп keycloak]
set -eu

: "${PGHOST:=postgres}"
: "${PGUSER:=radar}"
: "${BACKUP_DIR:=/backups}"
CHECK_DB="radar_restore_check"
CHECK_KC="keycloak_restore_check"

latest() {
    find "$BACKUP_DIR" -maxdepth 1 -name "$1-*.dump" -type f | sort | tail -1
}

RADAR_FILE="${1:-$(latest radar)}"
KC_FILE="${2:-$(latest keycloak)}"
for FILE in "$RADAR_FILE" "$KC_FILE"; do
    if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
        echo "Не найден дамп для проверки в $BACKUP_DIR (нужны radar-*.dump и keycloak-*.dump)" >&2
        exit 1
    fi
done

q() {
    psql --host="$PGHOST" --username="$PGUSER" --dbname="$1" -Atc "$2"
}

# Временные базы удаляются и при ошибке: иначе следующая проверка упадёт на createdb,
# а копия базы с данными останется лежать на сервере.
cleanup() {
    dropdb --host="$PGHOST" --username="$PGUSER" --if-exists "$CHECK_DB"
    dropdb --host="$PGHOST" --username="$PGUSER" --if-exists "$CHECK_KC"
}
trap cleanup EXIT
cleanup

echo "Проверяем $RADAR_FILE"
createdb --host="$PGHOST" --username="$PGUSER" "$CHECK_DB"
pg_restore --host="$PGHOST" --username="$PGUSER" --dbname="$CHECK_DB" --no-owner \
    --exit-on-error "$RADAR_FILE"

# Сверяем с рабочей базой, а не с числом из головы: новая таблица не сделает проверку мягче.
TABLES=$(q "$CHECK_DB" "select count(*) from pg_tables where schemaname='public'")
LIVE_TABLES=$(q radar "select count(*) from pg_tables where schemaname='public'")
REVISION=$(q "$CHECK_DB" "select version_num from alembic_version")
INTERACTIONS=$(q "$CHECK_DB" "select count(*) from interaction")
TRANSITIONS=$(q "$CHECK_DB" "select count(*) from transition")
echo "Таблиц: $TABLES из $LIVE_TABLES, миграция $REVISION," \
    "взаимодействий: $INTERACTIONS, переходов: $TRANSITIONS"

echo "Проверяем $KC_FILE"
createdb --host="$PGHOST" --username="$PGUSER" "$CHECK_KC"
pg_restore --host="$PGHOST" --username="$PGUSER" --dbname="$CHECK_KC" --no-owner \
    --exit-on-error "$KC_FILE"
REALM=$(q "$CHECK_KC" "select count(*) from realm where name='radar-vuzov'")
KC_USERS=$(q "$CHECK_KC" "select count(*) from user_entity e join realm r on r.id = e.realm_id where r.name='radar-vuzov'")
echo "Realm radar-vuzov: $REALM, пользователей в нём: $KC_USERS"

if [ "$TABLES" -ne "$LIVE_TABLES" ] || [ "$INTERACTIONS" -lt 1 ] || [ "$REALM" -ne 1 ] \
    || [ "$KC_USERS" -lt 1 ]; then
    echo "Восстановление неполное: проверьте дампы" >&2
    exit 1
fi
echo "Восстановление проверено"
