"""Условные запросы: ответ с ETag, а повтор без изменений — короткий `304 Not Modified`.

Браузер сам хранит ответ и сам переспрашивает с `If-None-Match`, поэтому открытая заново
карточка и справочники достаются из его кэша, а приложению фронтенда ничего делать не нужно.
Всё, что зависит от прав, помечено `private, no-cache`: ответ можно хранить только у себя
и только с проверкой на сервере — иначе смена области видимости показывала бы старые данные.
"""

import hashlib
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, Response
from pydantic import TypeAdapter

from app.core.cache import get_cache

# Хранить можно, но каждый раз спрашивать сервер: данные зависят от прав и меняются.
REVALIDATE = "private, no-cache"
# Только для файлов без прав доступа (картинки справки): содержимое по адресу не меняется.
# Вложения и отчёты так помечать нельзя: после потери доступа браузер ещё сутки отдавал бы
# копию, не спрашивая сервер. Им — REVALIDATE и ETag: повтор стоит один короткий 304.
IMMUTABLE = "private, max-age=86400, immutable"
NOT_MODIFIED = 304
# Для OpenAPI: у условного ответа есть второй возможный статус.
NOT_MODIFIED_RESPONSE: dict[int | str, dict[str, Any]] = {
    NOT_MODIFIED: {"description": "С прошлого запроса ничего не изменилось"}
}


def etag_of(value: bytes | str) -> str:
    digest = hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()
    return f'"{digest[:32]}"'


def fresh_for_client(request: Request, etag: str) -> bool:
    """Клиент прислал тот же ETag: у него уже есть этот ответ."""
    header = request.headers.get("if-none-match", "")
    return any(tag.strip().removeprefix("W/") == etag for tag in header.split(",") if tag.strip())


def conditional(
    request: Request, body: bytes, *, cache_control: str = REVALIDATE, etag: str | None = None
) -> Response:
    tag = etag or etag_of(body)
    headers = {"ETag": tag, "Cache-Control": cache_control}
    if fresh_for_client(request, tag):
        return Response(status_code=NOT_MODIFIED, headers=headers)
    return Response(content=body, media_type="application/json", headers=headers)


async def cached_json[T](
    request: Request,
    namespace: str,
    suffix: str,
    adapter: TypeAdapter[T],
    build: Callable[[], Awaitable[T]],
    ttl: int,
) -> Response:
    """Ответ из кэша поколения `namespace`, а если его там нет — собранный и положенный туда."""
    cache = get_cache()
    key = f"cache:{namespace}:{await cache.generation(namespace)}:{suffix}"
    body = await cache.get(key)
    if body is None:
        body = adapter.dump_json(await build()).decode()
        await cache.set(key, body, ttl)
    return conditional(request, body.encode())
