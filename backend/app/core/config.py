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
    # Каталог вложений; в облаке заменяется на S3 за тем же интерфейсом Storage.
    upload_dir: str = "storage/uploads"
    max_upload_mb: int = 25
    log_level: str = "INFO"
    version: str = "0.1.0"

    @model_validator(mode="after")
    def forbid_dev_auth_in_production(self) -> Self:
        # Режим X-Dev-User обходит Keycloak, поэтому в продакшене он запрещён (ADR-011).
        if self.app_env == "production" and self.auth_mode == "dev":
            raise ValueError("AUTH_MODE=dev запрещён при APP_ENV=production")
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
