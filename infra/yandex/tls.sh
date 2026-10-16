#!/bin/sh
# Сертификат Let's Encrypt для стенда. Запускать из каталога infra на сервере.
#
#   sh yandex/tls.sh issue   — первый выпуск, пока nginx ещё не запущен (certbot сам слушает 80 порт)
#   sh yandex/tls.sh renew   — продление через работающий nginx; ставится в cron раз в неделю
#
# Адрес берётся из PUBLIC_URL в infra/.env. nginx ждёт fullchain.pem и privkey.pem в CERTS_DIR;
# certbot хранит их символьными ссылками, которые внутри контейнера nginx никуда не ведут,
# поэтому файлы копируются в CERTS_DIR настоящими.
set -eu

cd "$(dirname "$0")/.."
# shellcheck disable=SC1091
set -a && . ./.env && set +a

HOST=$(printf '%s' "${PUBLIC_URL:?PUBLIC_URL в .env}" | sed -E 's#^https?://##; s#/.*$##')
LE_DIR="${LE_DIR:-/srv/radar/letsencrypt}"
CERTS_DIR="${CERTS_DIR:?CERTS_DIR в .env}"
CERTBOT="certbot/certbot:v4.2.0@sha256:9626d72120577cf72da4fc7948806e9993598981720a4cbe04340a502468d67b"
COMPOSE="docker compose -f docker-compose.prod.yml -f docker-compose.yandex.yml --env-file .env"
# Почта для писем Let's Encrypt об истечении; без неё сертификат выпускается так же.
if [ -n "${LETSENCRYPT_EMAIL:-}" ]; then
    ACCOUNT="--email $LETSENCRYPT_EMAIL"
else
    ACCOUNT="--register-unsafely-without-email"
fi

install_certs() {
    mkdir -p "$CERTS_DIR"
    # Каталог live/ certbot создаёт под root с правами 700, поэтому копирует тот же контейнер,
    # а владельцем файлов становится пользователь, запустивший скрипт (в том числе из cron).
    docker run --rm --entrypoint sh -v "$LE_DIR:/etc/letsencrypt:ro" -v "$CERTS_DIR:/out" \
        "$CERTBOT" -c "cp -L /etc/letsencrypt/live/$HOST/fullchain.pem /etc/letsencrypt/live/$HOST/privkey.pem /out/ \
            && chmod 600 /out/privkey.pem && chown $(id -u):$(id -g) /out/fullchain.pem /out/privkey.pem"
    echo "Сертификат для $HOST лежит в $CERTS_DIR"
}

case "${1:-}" in
    issue)
        mkdir -p "$LE_DIR"
        # shellcheck disable=SC2086
        docker run --rm -p 80:80 -v "$LE_DIR:/etc/letsencrypt" "$CERTBOT" certonly \
            --standalone --non-interactive --agree-tos $ACCOUNT -d "$HOST"
        install_certs
        ;;
    renew)
        # Каталог проверки — тот же том, который nginx отдаёт по /.well-known/acme-challenge/.
        docker run --rm -v "$LE_DIR:/etc/letsencrypt" \
            -v radar-vuzov-prod_certbot-www:/var/www/certbot "$CERTBOT" renew \
            --webroot -w /var/www/certbot --non-interactive
        install_certs
        $COMPOSE exec -T web nginx -s reload
        ;;
    *)
        echo "Использование: sh yandex/tls.sh issue|renew" >&2
        exit 2
        ;;
esac
