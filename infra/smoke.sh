#!/bin/sh
# Проверка стенда после деплоя: живо ли приложение и закрыт ли доступ без токена.
# Запуск: sh infra/smoke.sh https://radar.example.ru
set -eu

BASE_URL="${1:-${PUBLIC_URL:-http://127.0.0.1:8000}}"
FAILED=0

check() {
    name="$1"
    expected="$2"
    url="$3"
    # curl при недоступном узле и печатает 000, и возвращает ошибку: подстраховка через || дала бы
    # «000000», поэтому ошибку глушим, а пустой ответ считаем нулевым кодом сами.
    code=$(curl -sk -o /tmp/smoke-body -w '%{http_code}' --max-time 20 "$url" 2>/dev/null) || true
    [ -n "$code" ] || code="000"
    if [ "$code" = "$expected" ]; then
        echo "ок      $name ($code)"
    else
        echo "ОШИБКА  $name: ожидали $expected, получили $code — $url" >&2
        FAILED=1
    fi
}

echo "Стенд: $BASE_URL"

check "состояние сервиса" 200 "$BASE_URL/api/health"
check "Swagger UI" 200 "$BASE_URL/api/docs"
check "схема OpenAPI" 200 "$BASE_URL/api/openapi.json"
check "описание OIDC" 200 "$BASE_URL/auth/realms/radar-vuzov/.well-known/openid-configuration"
# Без токена API обязан отвечать 401: это проверка того, что dev-режим не уехал на стенд.
check "доступ без токена закрыт" 401 "$BASE_URL/api/v1/me"

# База должна отвечать, иначе health вернул бы ok при мёртвой базе.
if curl -sk --max-time 20 "$BASE_URL/api/health" | grep -q '"database":"ok"'; then
    echo "ок      база отвечает"
else
    echo "ОШИБКА  база недоступна" >&2
    FAILED=1
fi

# Ответ об ошибке должен быть в формате problem+json с кодом из каталога.
if curl -sk --max-time 20 "$BASE_URL/api/v1/me" | grep -q '"code":"AUTH_REQUIRED"'; then
    echo "ок      ошибки в формате problem+json"
else
    echo "ОШИБКА  неожиданный формат ошибки" >&2
    FAILED=1
fi

[ "$FAILED" -eq 0 ] && echo "Стенд в порядке" || echo "Стенд поднялся с ошибками" >&2
exit "$FAILED"
