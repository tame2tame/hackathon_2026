"""Хранилище файлов: S3 за тем же интерфейсом, что и каталог на диске; клиент подменён, без сети."""

import io
from typing import Any

import pytest
from minio.error import S3Error

from app.core.config import Settings
from app.core.storage import LocalStorage, S3Storage
from app.modules.attachments.service import read_chunks


class FakeResponse:
    def __init__(self, data: bytes) -> None:
        self._buffer = io.BytesIO(data)
        self.released = False

    def read(self, amount: int | None = None) -> bytes:
        return self._buffer.read(amount)

    def close(self) -> None:
        return None

    def release_conn(self) -> None:
        self.released = True


class FakeMinio:
    """Ровно то, чем пользуется S3Storage: бакеты и объекты в памяти."""

    def __init__(self) -> None:
        self.buckets: set[str] = set()
        self.objects: dict[tuple[str, str], bytes] = {}
        self.created: list[str] = []
        self.responses: list[FakeResponse] = []

    def bucket_exists(self, bucket: str) -> bool:
        return bucket in self.buckets

    def make_bucket(self, bucket: str) -> None:
        self.buckets.add(bucket)
        self.created.append(bucket)

    def put_object(self, bucket: str, key: str, data: Any, length: int) -> None:
        self.objects[(bucket, key)] = data.read(length)

    def get_object(self, bucket: str, key: str) -> FakeResponse:
        if (bucket, key) not in self.objects:
            raise S3Error(None, "NoSuchKey", "Объекта нет", key, "request", "host")  # type: ignore[arg-type]
        response = FakeResponse(self.objects[(bucket, key)])
        self.responses.append(response)
        return response

    def remove_object(self, bucket: str, key: str) -> None:
        self.objects.pop((bucket, key), None)


def test_s3_storage_round_trip_creates_the_bucket_once() -> None:
    client = FakeMinio()
    storage = S3Storage(client, "radar-vuzov")  # type: ignore[arg-type]
    payload = b"%PDF-1.7 " + "договор".encode() * 50_000

    storage.save("interactions/1/a", io.BytesIO(payload))
    storage.save("interactions/1/b", io.BytesIO(b"second"))
    read_back = b"".join(read_chunks(storage.open("interactions/1/a")))

    assert read_back == payload
    assert client.created == ["radar-vuzov"]
    # Поток закрыт после чтения — соединение вернулось в пул клиента.
    assert client.responses[0].released is True
    assert storage.locate("interactions/1/a") == {
        "backend": "s3",
        "bucket": "radar-vuzov",
        "key": "interactions/1/a",
    }


def test_missing_object_looks_like_a_missing_file() -> None:
    storage = S3Storage(FakeMinio(), "radar-vuzov")  # type: ignore[arg-type]

    with pytest.raises(FileNotFoundError):
        storage.open("interactions/1/нет")


def test_deleted_object_is_gone() -> None:
    client = FakeMinio()
    storage = S3Storage(client, "radar-vuzov")  # type: ignore[arg-type]
    storage.save("reports/1.xlsx", io.BytesIO(b"PK"))

    storage.delete("reports/1.xlsx")

    assert client.objects == {}


def test_local_storage_describes_its_keys(tmp_path: Any) -> None:
    storage = LocalStorage(tmp_path)

    storage.check()

    assert storage.locate("interactions/1/a") == {"backend": "local", "key": "interactions/1/a"}


def test_s3_backend_needs_credentials() -> None:
    with pytest.raises(ValueError, match="S3_ACCESS_KEY"):
        Settings(storage_backend="s3", s3_access_key="", s3_secret_key="")
