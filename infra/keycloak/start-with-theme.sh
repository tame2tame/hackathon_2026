#!/usr/bin/env bash
set -euo pipefail
server_pid=''
setup_pid=''
cleanup() {
    trap - EXIT
    for child in "$setup_pid" "$server_pid"; do
        if [ -n "$child" ] && kill -0 "$child" 2>/dev/null; then
            kill -TERM "$child" 2>/dev/null || true
            wait "$child" 2>/dev/null || true
        fi
    done
    rm -f /tmp/radar-theme-ready
}
trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
rm -f /tmp/radar-theme-ready
/opt/keycloak/bin/kc.sh "$@" &
server_pid=$!
bash /opt/keycloak/radar/apply-theme.sh &
setup_pid=$!
# При ошибке применения контейнер завершается: деплой не должен молча оставить старую тему.
wait "$setup_pid"
setup_pid=''
touch /tmp/radar-theme-ready
wait "$server_pid"
