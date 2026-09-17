"""Серверный кэш справочников и рейтинга: Redis на стенде, память процесса в тестах.

Ключ кэша содержит номер поколения: изменение справочника увеличивает номер, и все ключи
прежнего поколения просто перестают попадаться — удалять их по шаблону не нужно, они истекут
сами. Так нет и гонки «прочитали старое, записали поверх нового»: запись всегда идёт в ключ
того поколения, которое читали.

Кэш — ускорение, а не источник правды: любая ошибка Redis означает «в кэше ничего нет»,
и ответ строится из базы как обычно.
"""

import logging
from functools import lru_cache
from typing import Protocol

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings

# Пространства имён: у каждого свой номер поколения.
CATALOGS = "catalogs"
RATING = "rating"

CATALOG_TTL = 300
RATING_TTL = 300

logger = logging.getLogger(__name__)


class Cache(Protocol):
    async def generation(self, namespace: str) -> int: ...

    async def get(self, key: str) -> str | None: ...

    async def set(self, key: str, value: str, ttl: int) -> None: ...

    async def bump(self, namespace: str) -> None: ...


class MemoryCache:
    """Кэш в памяти процесса: тесты и запуск без Redis. Срок жизни не нужен — процесс короткий."""

    def __init__(self) -> None:
        self._values: dict[str, str] = {}
        self._generations: dict[str, int] = {}

    async def generation(self, namespace: str) -> int:
        return self._generations.get(namespace, 0)

    async def get(self, key: str) -> str | None:
        return self._values.get(key)

    async def set(self, key: str, value: str, ttl: int) -> None:
        self._values[key] = value

    async def bump(self, namespace: str) -> None:
        self._generations[namespace] = self._generations.get(namespace, 0) + 1


class RedisCache:
    def __init__(self, client: Redis) -> None:
        self._client = client

    async def generation(self, namespace: str) -> int:
        try:
            value = await self._client.get(f"cache:gen:{namespace}")
        except RedisError:
            logger.warning("Кэш недоступен, отвечаем из базы", exc_info=True)
            return 0
        return int(value) if value else 0

    async def get(self, key: str) -> str | None:
        try:
            value: str | None = await self._client.get(key)
        except RedisError:
            logger.warning("Кэш недоступен, отвечаем из базы", exc_info=True)
            return None
        return value

    async def set(self, key: str, value: str, ttl: int) -> None:
        try:
            await self._client.set(key, value, ex=ttl)
        except RedisError:
            logger.warning("Кэш недоступен, ответ не сохранён", exc_info=True)

    async def bump(self, namespace: str) -> None:
        try:
            await self._client.incr(f"cache:gen:{namespace}")
        except RedisError:
            # Хуже всего здесь отдать пользователю ошибку из-за кэша: данные уже сохранены,
            # а устаревший ответ проживёт не дольше срока жизни ключа.
            logger.warning("Не удалось сбросить кэш", exc_info=True)


@lru_cache
def get_cache() -> Cache:
    settings = get_settings()
    if settings.app_env == "test" or not settings.redis_url:
        return MemoryCache()
    return RedisCache(Redis.from_url(settings.redis_url, decode_responses=True))


async def invalidate(namespace: str) -> None:
    """Справочник изменился: ответы прежнего поколения больше никому не достанутся."""
    await get_cache().bump(namespace)
