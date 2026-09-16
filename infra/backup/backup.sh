#!/bin/sh
# Ежедневный дамп базы. Запускается сервисом backup из docker-compose.
# Хранит последние KEEP_DAYS дампов, остальные удаляет.
set -eu

: "${PGHOST:=postgres}"
: "${PGUSER:=radar}"
: "${PGDATABASE:=radar}"
: "${BACKUP_DIR:=/backups}"
: "${KEEP_DAYS:=7}"

mkdir -p "$BACKUP_DIR"
STAMP=$(date -u +%Y%m%d-%H%M)
FILE="$BACKUP_DIR/radar-$STAMP.dump"

# Формат custom: восстанавливается выборочно и сжимается на лету.
pg_dump --host="$PGHOST" --username="$PGUSER" --dbname="$PGDATABASE" \
    --format=custom --file="$FILE"

echo "Дамп готов: $FILE ($(du -h "$FILE" | cut -f1))"

# Старые дампы удаляем, иначе диск кончится незаметно.
find "$BACKUP_DIR" -name 'radar-*.dump' -type f -mtime "+$KEEP_DAYS" -delete
echo "Дампов в каталоге: $(find "$BACKUP_DIR" -name 'radar-*.dump' | wc -l | tr -d ' ')"
