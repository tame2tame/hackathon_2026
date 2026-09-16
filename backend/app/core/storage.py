"""Хранилище вложений за узким интерфейсом: сейчас локальный каталог, в облаке — S3."""

import shutil
from functools import lru_cache
from pathlib import Path
from typing import BinaryIO, Protocol

from app.core.config import get_settings


class Storage(Protocol):
    """Минимум, который нужен вложениям. Ключ задаёт вызывающий код."""

    def save(self, key: str, source: BinaryIO) -> None: ...

    def open(self, key: str) -> BinaryIO: ...

    def delete(self, key: str) -> None: ...


class LocalStorage:
    """Файлы в каталоге на диске. Подходит для разработки и демо-стенда."""

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


@lru_cache
def get_storage() -> Storage:
    return LocalStorage(Path(get_settings().upload_dir))
