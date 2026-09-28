# Стенд в Yandex Cloud

Пошагово: от промокода до работающего `https://<ip>.sslip.io`. Общие сведения о профиле стенда,
ролях базы и резервных копиях — в [`DEPLOY.md`](DEPLOY.md); здесь только то, что относится
к Yandex Cloud.

Что получится: одна виртуальная машина с Docker (nginx, API, воркер, Keycloak, PostgreSQL, Redis,
заглушки LMS, сайта и мессенджеров), файлы вложений и отчётов — в бакете Yandex Object Storage,
сертификат Let's Encrypt на бесплатное имя `sslip.io`, которое указывает на IP машины.

Команды с пометкой **на Mac** выполняются у себя, **на сервере** — по SSH.

## 1. Облако

1. **Промокод.** Консоль → «Биллинг» → платёжный аккаунт → «Промокоды» → активировать. Грант
   ложится на платёжный аккаунт, к которому привязано облако.
2. **CLI** (на Mac, удобнее консоли):

   ```bash
   curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash
   exec -l $SHELL
   yc init            # вход через браузер, выбрать облако, каталог и зону ru-central1-a
   ```

3. **Статический IP** — чтобы адрес sslip.io не менялся при перезапуске машины:

   ```bash
   yc vpc address create --name radar-ip --external-ipv4 zone=ru-central1-a
   yc vpc address get radar-ip --format json | grep '"address"'
   ```

4. **Машина**: Ubuntu 24.04, 2 vCPU (100%), 8 ГБ памяти, 40 ГБ SSD. Меньше памяти не стоит:
   Keycloak и сборка образа на 4 ГБ упираются в своп.

   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/radar -N ""          # если ключа ещё нет
   yc compute instance create --name radar --zone ru-central1-a \
     --platform standard-v3 --cores 2 --core-fraction 100 --memory 8 \
     --create-boot-disk image-folder-id=standard-images,image-family=ubuntu-2404-lts,size=40,type=network-ssd \
     --network-interface subnet-name=default-ru-central1-a,nat-ip-version=ipv4,nat-address=<IP> \
     --ssh-key ~/.ssh/radar.pub
   ```

   Пользователь на машине — `yc-user`. Если в сети включены группы безопасности, откройте
   входящие 22, 80 и 443.

5. **Бакеты и ключ доступа.** Имена бакетов глобальные — добавьте свой суффикс.

   ```bash
   yc storage bucket create --name radar-vuzov-files-<суффикс>
   yc storage bucket update --name radar-vuzov-files-<суффикс> --versioning versioning-enabled
   yc storage bucket create --name radar-vuzov-backups-<суффикс>
   yc iam service-account create --name radar-storage
   SA_ID=$(yc iam service-account get radar-storage --format json | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
   yc resource-manager folder add-access-binding $(yc config get folder-id) \
     --role storage.editor --subject serviceAccount:$SA_ID
   yc iam access-key create --service-account-name radar-storage
   ```

   Последняя команда печатает `key_id` и `secret` — секрет показывается один раз, сохраните.
   Версионирование бакета файлов — это его резервная копия: удалённый или перезаписанный
   объект можно вернуть. Бакет копий хранит зашифрованные дампы базы (шаг 7).

## 2. Сервер

```bash
ssh -i ~/.ssh/radar yc-user@<IP>                                   # на Mac
curl -fsSL https://get.docker.com | sudo sh                        # на сервере
sudo usermod -aG docker yc-user && sudo mkdir -p /srv/radar && sudo chown yc-user /srv/radar
exit                                                               # перезайти, чтобы группа docker применилась
```

## 3. Код

Репозиторий приватный, поэтому на сервер едет архив ветки `main`, а не `git clone`:

```bash
cd /Users/olegbragin/Desktop/hackaton/hackathon_2026               # на Mac
git fetch origin && git archive --format=tar.gz -o /tmp/radar.tgz origin/main
scp -i ~/.ssh/radar /tmp/radar.tgz yc-user@<IP>:/srv/radar/
ssh -i ~/.ssh/radar yc-user@<IP> 'mkdir -p /srv/radar/hackathon_2026 && tar -xzf /srv/radar/radar.tgz -C /srv/radar/hackathon_2026'
```

## 4. Настройки

На сервере, в каталоге `infra`. Скрипт сам генерирует пароли базы, ключ шифрования и пароли
демо-входов и печатает их — сохраните пароли демо-входов для показа.

```bash
cd /srv/radar/hackathon_2026/infra
YC_S3_ACCESS_KEY=<key_id> YC_S3_SECRET_KEY=<secret> \
YC_S3_BUCKET=radar-vuzov-files-<суффикс> YC_OFFSITE_BUCKET=radar-vuzov-backups-<суффикс> \
  sh yandex/make-env.sh <IP>
```

Адрес стенда будет `https://<IP через дефисы>.sslip.io`, например `https://51-250-10-20.sslip.io`.
Существующий `.env` скрипт не перезаписывает: с его паролями уже создана база.

## 5. Сертификат

```bash
sh yandex/tls.sh issue          # на сервере, пока nginx не запущен: certbot сам слушает 80 порт
```

Если Let's Encrypt отказал из-за лимита на домен sslip.io, то же самое работает с `nip.io`:
поменяйте в `.env` `PUBLIC_URL` на `https://<IP через дефисы>.nip.io` и повторите.

Продление — раз в неделю через cron (`crontab -e`):

```text
0 4 * * 1 cd /srv/radar/hackathon_2026/infra && sh yandex/tls.sh renew >> /srv/radar/tls.log 2>&1
```

## 6. Интерфейс

Фронтенд собирается на Mac с адресом Keycloak стенда и отвозится готовым:

```bash
cd /Users/olegbragin/Desktop/hackaton/hackathon_2026/frontend      # на Mac
npm ci
VITE_AUTH_MODE=keycloak VITE_KEYCLOAK_URL=https://<адрес>.sslip.io/auth npm run build
ssh -i ~/.ssh/radar yc-user@<IP> 'mkdir -p /srv/radar/spa'
scp -i ~/.ssh/radar -r dist/. yc-user@<IP>:/srv/radar/spa/
```

## 7. Запуск

На сервере, в `/srv/radar/hackathon_2026/infra`:

```bash
alias dc='docker compose -f docker-compose.prod.yml -f docker-compose.yandex.yml --env-file .env'
dc build
dc up -d postgres redis
dc run --rm migrate
dc up -d
dc run --rm api python -m scripts.seed --full           # демо-данные, только на пустой базе
set -a && . ./.env && set +a && sh smoke.sh "$PUBLIC_URL"
```

Smoke-скрипт проверяет API, базу, хранилище (бакет), Swagger, Keycloak и то, что без входа API
отвечает `401`. Интерфейс — `https://<адрес>.sslip.io`, вход — `kam.demo`, `manager.demo`,
`admin.demo` с паролями из шага 4.

**Внешние копии базы** (по желанию, но без них потеря сервера — потеря данных). На Mac:

```bash
gpg --quick-generate-key radar-backup
gpg --export --armor radar-backup > /tmp/backup.asc
ssh -i ~/.ssh/radar yc-user@<IP> 'mkdir -p /srv/radar/hackathon_2026/infra/backup-keys'
scp -i ~/.ssh/radar /tmp/backup.asc yc-user@<IP>:/srv/radar/hackathon_2026/infra/backup-keys/
```

На сервере в `.env` — `BACKUP_GPG_PUBLIC_KEY=/keys/backup.asc`, затем `dc --profile offsite up -d`.
Закрытый ключ остаётся только у вас: им расшифровывается копия (`gpg --decrypt`).

## 8. Обновление

```bash
git fetch origin && git archive --format=tar.gz -o /tmp/radar.tgz origin/main     # на Mac
scp -i ~/.ssh/radar /tmp/radar.tgz yc-user@<IP>:/srv/radar/
```

```bash
cd /srv/radar/hackathon_2026 && tar -xzf /srv/radar/radar.tgz && cd infra           # на сервере
dc build && dc run --rm backup sh /scripts/backup.sh && dc run --rm migrate && dc up -d
```

Архив распаковывается поверх: `infra/.env`, сертификаты и данные лежат вне архива и не
затираются. Интерфейс пересобирается и отвозится так же, как в шаге 6.

## Что посмотреть, если не работает

- `dc ps` — все ли контейнеры `running`, `migrate` — `exited (0)`.
- `dc logs --tail 50 api` — `storage` в `/api/health` не `ok`: неверные ключи или имя бакета,
  или у сервисного аккаунта нет роли `storage.editor`.
- Вход крутится на странице Keycloak: интерфейс собран не с тем `VITE_KEYCLOAK_URL`.
- `dc logs keycloak` — Keycloak стартует до минуты; до этого nginx отвечает `502` на `/auth/`.
