#!/bin/sh
# Создаёт infra/.env для стенда в Yandex Cloud: все пароли и ключи генерируются здесь же.
#
#   YC_S3_ACCESS_KEY=... YC_S3_SECRET_KEY=... YC_S3_BUCKET=... YC_OFFSITE_BUCKET=... \
#     sh yandex/make-env.sh 51.250.10.20
#
# Аргумент — публичный IP сервера: из него получается адрес https://51-250-10-20.sslip.io.
# Существующий .env не перезаписывается: в нём пароли, с которыми уже создана база.
set -eu

cd "$(dirname "$0")/.."
IP="${1:?Укажите публичный IP сервера: sh yandex/make-env.sh 51.250.10.20}"
if [ -e .env ]; then
    echo "infra/.env уже есть — не перезаписываю. Удалите его сами, если база ещё не создана." >&2
    exit 1
fi

secret() { openssl rand -hex 20; }
# Пароль демо-входа: политика realm требует от 12 символов и не совпадать с логином.
demo() { printf 'Radar-%s' "$(openssl rand -hex 5)"; }
# Ключ Fernet — 32 случайных байта в base64 для URL.
fernet() { openssl rand 32 | base64 | tr '+/' '-_'; }

HOST="$(printf '%s' "$IP" | tr '.' '-').sslip.io"
umask 077
cat > .env <<EOF
# Стенд в Yandex Cloud. Создано yandex/make-env.sh $(date -u +%Y-%m-%d). В репозиторий не коммитить.
PUBLIC_URL=https://$HOST

POSTGRES_PASSWORD=$(secret)
APP_DB_PASSWORD=$(secret)
KEYCLOAK_DB_PASSWORD=$(secret)
PD_ENCRYPTION_KEY=$(fernet)

KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=$(secret)
DEMO_KAM_PASSWORD=$(demo)
DEMO_MANAGER_PASSWORD=$(demo)
DEMO_ADMIN_PASSWORD=$(demo)

# Файлы — в Yandex Object Storage (docker-compose.yandex.yml).
YC_S3_ACCESS_KEY=${YC_S3_ACCESS_KEY:-впишите-ключ}
YC_S3_SECRET_KEY=${YC_S3_SECRET_KEY:-впишите-секрет}
YC_S3_BUCKET=${YC_S3_BUCKET:-впишите-бакет}
YC_OFFSITE_BUCKET=${YC_OFFSITE_BUCKET:-впишите-бакет-копий}
# Своего MinIO в этом профиле нет, но базовый compose требует переменные: значения не используются.
MINIO_ROOT_USER=unused
MINIO_ROOT_PASSWORD=unused-minio

CERTS_DIR=/srv/radar/certs
SPA_DIR=/srv/radar/spa
# Открытый ключ для шифрования внешних копий: infra/backup-keys/backup.asc (см. docs/DEPLOY.md).
BACKUP_GPG_PUBLIC_KEY=
EOF
echo "Готово: infra/.env для https://$HOST"
echo "Пароли демо-входов (kam.demo, manager.demo, admin.demo):"
grep '^DEMO_' .env
