"""Хранилище файлов за узким интерфейсом: локальный каталог или S3-совместимое хранилище.

Вложения, отчёты и демо-файлы пишут через `Storage` и не знают, где лежат байты. На стенде это
MinIO, в облаке — любое S3-совместимое хранилище; для разработки без контейнеров — каталог на диске.
"""

import io
import os
import shutil
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO, Protocol

from app.core.config import get_settings

if TYPE_CHECKING:
    from minio import Minio
    from urllib3 import BaseHTTPResponse


class Storage(Protocol):
    """Минимум, который нужен вложениям. Ключ задаёт вызывающий код."""

    def save(self, key: str, source: BinaryIO) -> None: ...

    def open(self, key: str) -> BinaryIO: ...

    def delete(self, key: str) -> None: ...

    def locate(self, key: str) -> dict[str, str]:
        """Где лежит файл: по этим полям внешняя система найдёт его без нашего API."""
        ...

    def check(self) -> None:
        """Хранилище доступно на запись; иначе исключение."""
        ...


class LocalStorage:
    """Файлы в каталоге на диске. Подходит для разработки без контейнеров."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def _path(self, key: str) -> Path:
        path = (self._root / key).resolve()
        # Ключ приходит из кода, но проверка дешёвая и закрывает выход за каталог.
        if not path.is_relative_to(self._root):
            raise ValueError("Ключ ведёт за пределы хранилища.")
        return path

    def save(self, key: str, source: BinaryIO) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        source.seek(0)
        with path.open("wb") as target:
            shutil.copyfileobj(source, target)

    def open(self, key: str) -> BinaryIO:
        return self._path(key).open("rb")

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def locate(self, key: str) -> dict[str, str]:
        return {"backend": "local", "key": key}

    def check(self) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        if not os.access(self._root, os.W_OK):
            raise PermissionError(f"Каталог хранилища недоступен на запись: {self._root}")


class _ObjectStream(io.RawIOBase):
    """Поток объекта S3. Закрытие возвращает соединение в пул клиента."""

    def __init__(self, response: "BaseHTTPResponse") -> None:
        self._response = response

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: "memoryview | bytearray") -> int:  # type: ignore[override]
        chunk = self._response.read(len(buffer))
        buffer[: len(chunk)] = chunk
        return len(chunk)

    def close(self) -> None:
        if not self.closed:
            self._response.close()
            self._response.release_conn()
        super().close()


class S3Storage:
    """S3-совместимое хранилище: MinIO, Yandex Object Storage и другие."""

    def __init__(self, client: "Minio", bucket: str) -> None:
        self._client = client
        self._bucket = bucket
        self._bucket_ready = False

    def _ensure_bucket(self) -> None:
        # Бакет создаётся при первом обращении: стенду не нужен отдельный шаг установки.
        if self._bucket_ready:
            return
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)
        self._bucket_ready = True

    def save(self, key: str, source: BinaryIO) -> None:
        self._ensure_bucket()
        source.seek(0, os.SEEK_END)
        length = source.tell()
        source.seek(0)
        self._client.put_object(self._bucket, key, source, length=length)

    def open(self, key: str) -> BinaryIO:
        from minio.error import S3Error

        try:
            response = self._client.get_object(self._bucket, key)
        except S3Error as error:
            if error.code in {"NoSuchKey", "NoSuchBucket"}:
                # Сервисы отвечают на OSError «не найдено», как для отсутствующего файла на диске.
                raise FileNotFoundError(key) from error
            raise
        return io.BufferedReader(_ObjectStream(response))

    def delete(self, key: str) -> None:
        self._ensure_bucket()
        self._client.remove_object(self._bucket, key)

    def locate(self, key: str) -> dict[str, str]:
        return {"backend": "s3", "bucket": self._bucket, "key": key}

    def check(self) -> None:
        self._bucket_ready = False
        self._ensure_bucket()


@lru_cache
def get_storage() -> Storage:
    settings = get_settings()
    if settings.storage_backend == "s3":
        from minio import Minio

        client = Minio(
            settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            secure=settings.s3_secure,
            region=settings.s3_region or None,
        )
        return S3Storage(client, settings.s3_bucket)
    return LocalStorage(Path(settings.upload_dir))
