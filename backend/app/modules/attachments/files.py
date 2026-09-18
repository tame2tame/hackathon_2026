"""Белый список типов файлов из ТЗ. Проверяются и расширение, и сигнатура содержимого."""

from dataclasses import dataclass
from pathlib import Path

ZIP = b"PK\x03\x04"
OLE2 = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
FORBIDDEN_IN_NAME = '<>:"|?*\\/'


@dataclass(frozen=True, slots=True)
class FileType:
    extensions: tuple[str, ...]
    mime: str
    signatures: tuple[bytes, ...]


# Форматы перечислены в ТЗ. docx и xlsx — zip-контейнеры, doc и xls — контейнеры OLE2.
ALLOWED: tuple[FileType, ...] = (
    FileType((".png",), "image/png", (b"\x89PNG\r\n\x1a\n",)),
    FileType((".jpg", ".jpeg"), "image/jpeg", (b"\xff\xd8\xff",)),
    FileType((".pdf",), "application/pdf", (b"%PDF-",)),
    FileType((".zip",), "application/zip", (ZIP, b"PK\x05\x06", b"PK\x07\x08")),
    FileType((".gz", ".gzip"), "application/gzip", (b"\x1f\x8b",)),
    FileType((".rar",), "application/vnd.rar", (b"Rar!\x1a\x07\x00", b"Rar!\x1a\x07\x01\x00")),
    FileType((".doc",), "application/msword", (OLE2,)),
    FileType(
        (".docx",),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        (ZIP,),
    ),
    FileType((".xls",), "application/vnd.ms-excel", (OLE2,)),
    FileType(
        (".xlsx",),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        (ZIP,),
    ),
)

SIGNATURE_BYTES = max(len(signature) for file_type in ALLOWED for signature in file_type.signatures)
EXTENSIONS = sorted(extension for file_type in ALLOWED for extension in file_type.extensions)


def match(file_name: str, head: bytes) -> FileType | None:
    """Тип по расширению, подтверждённый началом файла: exe, переименованный в pdf, не пройдёт."""
    suffix = Path(safe_name(file_name)).suffix.lower()
    for file_type in ALLOWED:
        if suffix in file_type.extensions:
            return file_type if head.startswith(file_type.signatures) else None
    return None


def safe_name(file_name: str) -> str:
    """Имя без путей, управляющих символов и лишних точек по краям."""
    tail = file_name.replace("\\", "/").rsplit("/", 1)[-1]
    cleaned = "".join(ch for ch in tail if ch.isprintable() and ch not in FORBIDDEN_IN_NAME)
    return cleaned.strip(" .")[:255] or "file"
