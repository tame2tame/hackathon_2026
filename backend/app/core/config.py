"""Настройки приложения из переменных окружения и файла .env."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["local", "test", "production"] = "local"
    auth_mode: Literal["keycloak", "dev"] = "keycloak"
    # Порт из docker compose: 5432 на машине разработчика обычно занят локальным PostgreSQL.
    database_url: str = "postgresql+asyncpg://radar:radar@127.0.0.1:55432/radar"
    cors_origins: str = ""
    keycloak_issuer: str = "http://127.0.0.1:8080/realms/radar-vuzov"
    # Внутри docker compose ключи берутся по внутреннему адресу, а издатель в токене — внешний.
    keycloak_jwks_url: str = ""
    keycloak_audience: str = "radar-api"
    # Пустой адрес переводит события в память процесса: так работают тесты и запуск без Redis.
    redis_url: str = "redis://127.0.0.1:6379/0"
    # Адреса внешних систем; на демо-стенде это моки из backend/mocks.
    lms_base_url: str = "http://127.0.0.1:8100"
    site_base_url: str = "http://127.0.0.1:8101"
    # Каналы уведомлений по умолчанию; на демо-стенде это заглушка мессенджеров и Mailpit.
    telegram_api_url: str = "http://127.0.0.1:8102"
    max_api_url: str = "http://127.0.0.1:8102"
    smtp_host: str = "127.0.0.1"
    smtp_port: int = 1025
    smtp_sender: str = "radar@example.com"
    # Адрес интерфейса: из него строится ссылка на карточку в тексте уведомления.
    public_url: str = "http://127.0.0.1:5173"
    # Ключ Fernet для email и телефонов контактов вуза; пустой означает «шифрование не настроено».
    pd_encryption_key: str = ""
    # Хранилище файлов: local — каталог upload_dir, s3 — MinIO или другое S3-совместимое хранилище.
    storage_backend: Literal["local", "s3"] = "local"
    upload_dir: str = "storage/uploads"
    s3_endpoint: str = "127.0.0.1:9000"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket: str = "radar-vuzov"
    s3_secure: bool = False
    s3_region: str = ""
    max_upload_mb: int = 25
    log_level: str = "INFO"
    version: str = "0.1.0"

    @model_validator(mode="after")
    def forbid_dev_auth_in_production(self) -> Self:
        # Режим X-Dev-User обходит Keycloak, поэтому в продакшене он запрещён (ADR-011).
        if self.app_env == "production" and self.auth_mode == "dev":
            raise ValueError("AUTH_MODE=dev запрещён при APP_ENV=production")
        return self

    @model_validator(mode="after")
    def require_s3_credentials(self) -> Self:
        if self.storage_backend == "s3" and not (self.s3_access_key and self.s3_secret_key):
            raise ValueError("STORAGE_BACKEND=s3 требует S3_ACCESS_KEY и S3_SECRET_KEY")
        return self

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def jwks_url(self) -> str:
        return self.keycloak_jwks_url or f"{self.keycloak_issuer}/protocol/openid-connect/certs"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
