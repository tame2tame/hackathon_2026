#!/usr/bin/env bash
# Только оформление существующего realm; полный импорт не обновляет его настройки.
set -euo pipefail
: "${KC_BOOTSTRAP_ADMIN_USERNAME:?Не задан администратор Keycloak}"
: "${KC_BOOTSTRAP_ADMIN_PASSWORD:?Не задан пароль администратора Keycloak}"
cli="${KEYCLOAK_BIN_DIR:-/opt/keycloak/bin}/kcadm.sh"
umask 077
config=$(mktemp "${TMPDIR:-/tmp}/radar-kcadm.XXXXXX")
trap 'rm -f "$config"' EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
# CLI читает пароль из окружения: он не появляется в аргументах процесса и логах.
export KC_CLI_PASSWORD="$KC_BOOTSTRAP_ADMIN_PASSWORD"
attempt=0
until "$cli" config credentials --config "$config" --server http://127.0.0.1:8080 \
    --realm master --user "$KC_BOOTSTRAP_ADMIN_USERNAME" >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge "${RADAR_THEME_ATTEMPTS:-60}" ]; then
        echo 'Не удалось применить тему: проверьте запуск Keycloak и учётные данные администратора.' >&2
        exit 1
    fi
    sleep "${RADAR_THEME_RETRY_SECONDS:-2}"
done
# PUT передаёт только четыре поля, сохраняя пользователей, клиентов и политики realm.
if ! "$cli" update realms/radar-vuzov --config "$config" --no-merge \
    -s loginTheme=radar -s internationalizationEnabled=true \
    -s 'supportedLocales=["ru"]' -s defaultLocale=ru >/dev/null 2>&1; then
    echo 'Не удалось обновить тему realm radar-vuzov.' >&2
    exit 1
fi
echo 'Тема входа radar и русский язык применены.'
