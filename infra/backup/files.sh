#!/bin/sh
# Ежедневная копия файлов из MinIO. Запускается сервисом backup-files из docker-compose.
# Дамп базы файлов не содержит: без этой копии восстановленная запись ссылается на пустоту.
# Скрипт работает внутри образа MinIO, где из утилит есть только sh, mc, ls, du, wc и mkdir.
#
# Если задан OFFSITE_URL, зашифрованные копии из $BACKUP_ROOT/offsite (их готовит backup.sh)
# ещё и отвозятся во внешнее S3-хранилище: копия на том же сервере не спасёт от потери сервера.
set -eu

: "${S3_ENDPOINT:=http://minio:9000}"
: "${S3_BUCKET:=radar-vuzov}"
: "${BACKUP_ROOT:=/backups}"
: "${BACKUP_DIR:=$BACKUP_ROOT/files}"
: "${MINIO_ROOT_USER:?логин MinIO}"
: "${MINIO_ROOT_PASSWORD:?пароль MinIO}"
: "${OFFSITE_URL:=}"
ALIAS=source

# Ключи пишем в конфиг mc, а не в аргументы `mc alias set`: аргументы видны в списке
# процессов любому пользователю сервера.
MC_CONFIG_DIR=$(mktemp -d)
trap 'rm -rf "$MC_CONFIG_DIR"' EXIT
alias_json() {
    printf '"%s":{"url":"%s","accessKey":"%s","secretKey":"%s","api":"s3v4","path":"auto"}' \
        "$1" "$2" "$3" "$4"
}
{
    printf '{"version":"10","aliases":{'
    alias_json "$ALIAS" "$S3_ENDPOINT" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"
    if [ -n "$OFFSITE_URL" ]; then
        printf ','
        alias_json offsite "$OFFSITE_URL" "${OFFSITE_ACCESS_KEY:?ключ внешнего хранилища}" \
            "${OFFSITE_SECRET_KEY:?секрет внешнего хранилища}"
    fi
    printf '}}'
} >"$MC_CONFIG_DIR/config.json"
chmod 600 "$MC_CONFIG_DIR/config.json"
mc() {
    command mc --config-dir "$MC_CONFIG_DIR" "$@"
}

mkdir -p "$BACKUP_DIR"

# На свежем стенде бакет появляется при первой загрузке файла: копировать пока нечего.
if mc ls "$ALIAS/$S3_BUCKET" >/dev/null 2>&1; then
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
else
    echo "Бакет $S3_BUCKET ещё не создан: файлов нет, копия не нужна"
fi

if [ -n "$OFFSITE_URL" ]; then
    : "${OFFSITE_BUCKET:?бакет внешнего хранилища}"
    if [ -d "$BACKUP_ROOT/offsite" ]; then
        # Только готовые .gpg: недописанные .partial уедут в следующий раз.
        mc mirror --quiet --overwrite --exclude '*.partial' \
            "$BACKUP_ROOT/offsite" "offsite/$OFFSITE_BUCKET"
        echo "Внешняя копия обновлена: $(mc ls "offsite/$OFFSITE_BUCKET" | wc -l | tr -d ' ') файлов"
    else
        echo "ОШИБКА  внешнее хранилище задано, но зашифрованных копий нет:" \
            "проверьте BACKUP_GPG_PUBLIC_KEY у сервиса backup" >&2
        exit 1
    fi
fi
