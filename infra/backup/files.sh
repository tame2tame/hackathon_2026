#!/bin/sh
# Ежедневная копия файлов из MinIO. Запускается сервисом backup-files из docker-compose.
# Дамп базы файлов не содержит: без этой копии восстановленная запись ссылается на пустоту.
# Скрипт работает внутри образа MinIO, где из утилит есть только sh, mc, ls, du, wc и mkdir.
set -eu

: "${S3_ENDPOINT:=http://minio:9000}"
: "${S3_BUCKET:=radar-vuzov}"
: "${BACKUP_DIR:=/backups/files}"
: "${MINIO_ROOT_USER:?логин MinIO}"
: "${MINIO_ROOT_PASSWORD:?пароль MinIO}"
ALIAS=backup-source

mc alias set "$ALIAS" "$S3_ENDPOINT" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null
mkdir -p "$BACKUP_DIR"

# На свежем стенде бакет появляется при первой загрузке файла: копировать пока нечего.
if ! mc ls "$ALIAS/$S3_BUCKET" >/dev/null 2>&1; then
    echo "Бакет $S3_BUCKET ещё не создан: файлов нет, копия не нужна"
    exit 0
fi

# Без --remove: файл, удалённый из бакета по ошибке, остаётся в копии. Вложения система
# не удаляет, поэтому копия растёт ровно на столько, сколько загрузили.
mc mirror --quiet --overwrite "$ALIAS/$S3_BUCKET" "$BACKUP_DIR"

REMOTE=$(mc ls --recursive "$ALIAS/$S3_BUCKET" | wc -l | tr -d ' ')
LOCAL=$(mc ls --recursive "$BACKUP_DIR" | wc -l | tr -d ' ')
echo "Объектов в хранилище: $REMOTE, в копии: $LOCAL ($(du -sh "$BACKUP_DIR" | cut -f1))"

if [ "$LOCAL" -lt "$REMOTE" ]; then
    echo "ОШИБКА  копия неполная: в хранилище $REMOTE объектов, скопировано $LOCAL" >&2
    exit 1
fi
