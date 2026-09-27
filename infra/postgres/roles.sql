-- Роли базы стенда. Выполняется образом postgres один раз, при создании пустого тома.
--
-- radar      — владелец схемы: под ним идут только миграции (сервис migrate) и резервные копии.
-- radar_app  — API и воркер: читают и пишут данные, но не владеют таблицами. Поэтому не могут
--              отключить триггеры, удалить таблицу или очистить историю переходов и аудит.
-- keycloak   — отдельная база и отдельный пароль: утечка одного пароля не открывает другую базу.
--
-- Пароли приходят из окружения контейнера через \getenv: в файле их нет, а .sql, в отличие
-- от .sh, не зависит от бита исполнения на смонтированном томе.
\getenv app_password APP_DB_PASSWORD
\getenv keycloak_password KEYCLOAK_DB_PASSWORD

CREATE ROLE radar_app LOGIN PASSWORD :'app_password';
CREATE ROLE keycloak LOGIN PASSWORD :'keycloak_password';
CREATE DATABASE keycloak OWNER keycloak;

REVOKE ALL ON DATABASE keycloak FROM PUBLIC;
REVOKE ALL ON DATABASE radar FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE radar TO radar_app;
GRANT USAGE ON SCHEMA public TO radar_app;

-- Таблицы создаёт миграция под владельцем, права на них radar_app получает сразу.
-- Историю переходов и аудит миграция 5c0d9e3a7b21 затем оставляет только на дописывание.
ALTER DEFAULT PRIVILEGES FOR ROLE radar IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO radar_app;
ALTER DEFAULT PRIVILEGES FOR ROLE radar IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO radar_app;
