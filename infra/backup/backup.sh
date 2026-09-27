#!/bin/sh
# Ежедневный дамп баз. Запускается сервисом backup из docker-compose.
# Хранит последние KEEP_DAYS дампов, остальные удаляет.
#
# Копируются обе базы: radar (данные системы) и keycloak (пользователи, роли, пароли входа).
# Без второй восстановленный стенд не пустит ни одного пользователя.
#
# Если задан BACKUP_GPG_PUBLIC_KEY (файл открытого ключа), дампы и архив файлов ещё и
# шифруются в $BACKUP_DIR/offsite — оттуда их забирает во внешнее хранилище files.sh.
# Закрытый ключ на сервере не хранится: утечка сервера не раскрывает внешние копии.
set -eu

: "${PGHOST:=postgres}"
: "${PGUSER:=radar}"
: "${BACKUP_DATABASES:=radar keycloak}"
: "${BACKUP_DIR:=/backups}"
: "${KEEP_DAYS:=7}"
: "${BACKUP_GPG_PUBLIC_KEY:=}"

mkdir -p "$BACKUP_DIR"
STAMP=$(date -u +%Y%m%d-%H%M)

for DB in $BACKUP_DATABASES; do
    FILE="$BACKUP_DIR/$DB-$STAMP.dump"
    # Пишем во временный файл и переименовываем в конце: оборванный дамп не должен
    # выглядеть свежей копией для restore-check и для глаз администратора.
    pg_dump --host="$PGHOST" --username="$PGUSER" --dbname="$DB" \
        --format=custom --file="$FILE.partial"
    mv "$FILE.partial" "$FILE"
    echo "Дамп готов: $FILE ($(du -h "$FILE" | cut -f1))"
done

if [ -n "$BACKUP_GPG_PUBLIC_KEY" ]; then
    OFFSITE="$BACKUP_DIR/offsite"
    mkdir -p "$OFFSITE"
    GNUPGHOME=$(mktemp -d)
    export GNUPGHOME
    trap 'rm -rf "$GNUPGHOME"' EXIT
    encrypt() {
        gpg --batch --quiet --trust-model always --recipient-file "$BACKUP_GPG_PUBLIC_KEY" \
            --output "$2.partial" --encrypt "$1"
        mv "$2.partial" "$2"
    }
    for DB in $BACKUP_DATABASES; do
        encrypt "$BACKUP_DIR/$DB-$STAMP.dump" "$OFFSITE/$DB-$STAMP.dump.gpg"
    done
    # Файлы вложений кладёт в $BACKUP_DIR/files сервис backup-files.
    if [ -d "$BACKUP_DIR/files" ]; then
        tar -C "$BACKUP_DIR" -cf "$OFFSITE/files-$STAMP.tar" files
        encrypt "$OFFSITE/files-$STAMP.tar" "$OFFSITE/files-$STAMP.tar.gpg"
        rm -f "$OFFSITE/files-$STAMP.tar"
    fi
    find "$OFFSITE" -name '*.gpg' -type f -mtime "+$KEEP_DAYS" -delete
    echo "Зашифрованные копии для внешнего хранилища: $OFFSITE"
fi

# Старые дампы и брошенные недописанные удаляем, иначе диск кончится незаметно.
find "$BACKUP_DIR" -maxdepth 1 -name '*.dump' -type f -mtime "+$KEEP_DAYS" -delete
find "$BACKUP_DIR" -maxdepth 1 -name '*.partial' -type f -mmin +1440 -delete
echo "Дампов в каталоге: $(find "$BACKUP_DIR" -maxdepth 1 -name '*.dump' | wc -l | tr -d ' ')"
