"""Вложения: загрузка с проверкой типа и размера, список и чтение файла."""

import hashlib
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import BinaryIO

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings, get_settings
from app.core.errors import AppError, ErrorCode, FieldError
from app.core.scope import apply_interaction_scope, visible_interaction
from app.core.security import CurrentUser
from app.core.storage import Storage, get_storage
from app.modules.attachments import files
from app.modules.audit.models import AuditLog
from app.modules.integrations.outbox import mark_changed
from app.modules.interactions.models import Attachment, Interaction
from app.modules.radar.service import recompute_signals
from app.modules.workflow.models import Stage

CHUNK_BYTES = 1024 * 1024
ATTACHMENT_NOT_FOUND = "Вложение не найдено или недоступно."


async def _known_document_types(session: AsyncSession, version_id: uuid.UUID) -> set[str]:
    """Типы документов, которые требует хотя бы один этап версии процесса."""
    rows = await session.scalars(
        select(Stage.required_document_types).where(Stage.version_id == version_id)
    )
    return {document_type for row in rows for document_type in row}


async def _checked_file(upload: UploadFile, settings: Settings) -> tuple[files.FileType, str, int]:
    """Читает файл целиком: считает размер и sha256, проверяет лимит, расширение и сигнатуру."""
    digest = hashlib.sha256()
    size = 0
    head = b""
    while chunk := await upload.read(CHUNK_BYTES):
        if not head:
            head = chunk[: files.SIGNATURE_BYTES]
        size += len(chunk)
        if size > settings.max_upload_bytes:
            raise AppError(ErrorCode.FILE_TOO_LARGE, f"Файл больше {settings.max_upload_mb} МБ.")
        digest.update(chunk)
    if size == 0:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Файл пустой.",
            errors=[FieldError(field="file", message="Пустой файл")],
        )
    file_type = files.match(upload.filename or "", head)
    if file_type is None:
        raise AppError(
            ErrorCode.FILE_TYPE_NOT_ALLOWED,
            f"Допустимы только файлы: {', '.join(files.EXTENSIONS)}.",
        )
    return file_type, digest.hexdigest(), size


async def upload_attachment(
    session: AsyncSession,
    user: CurrentUser,
    interaction_id: uuid.UUID,
    upload: UploadFile,
    document_type: str | None,
    trace_id: str | None = None,
    now: datetime | None = None,
    storage: Storage | None = None,
    settings: Settings | None = None,
) -> Attachment:
    now = now or datetime.now(UTC)
    settings = settings or get_settings()
    storage = storage or get_storage()

    interaction = await visible_interaction(session, user, interaction_id)
    document_type = document_type.strip() if document_type else None
    if document_type:
        known = await _known_document_types(session, interaction.workflow_version_id)
        if document_type not in known:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                f"Неизвестный тип документа. Возможные: {', '.join(sorted(known))}.",
                errors=[FieldError(field="document_type", message="Неизвестный тип документа")],
            )
    file_type, sha256, size = await _checked_file(upload, settings)

    attachment_id = uuid.uuid4()
    storage_key = f"interactions/{interaction_id}/{attachment_id}"
    # Файл пишется до записи в БД: при отказе хранилища в базе не останется ссылки в никуда.
    await run_in_threadpool(storage.save, storage_key, upload.file)

    attachment = Attachment(
        id=attachment_id,
        interaction_id=interaction.id,
        stage_id=interaction.current_stage_id,
        document_type=document_type,
        file_name=files.safe_name(upload.filename or "file"),
        mime_type=file_type.mime,
        size_bytes=size,
        sha256=sha256,
        storage_key=storage_key,
        uploaded_by=user.id,
        uploaded_at=now,
    )
    session.add(attachment)
    interaction.last_activity_at = now
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="attachment.upload",
            entity_kind="attachment",
            entity_id=attachment_id,
            after={
                "interaction_id": str(interaction.id),
                "document_type": document_type,
                "size_bytes": size,
            },
            trace_id=trace_id,
        )
    )
    await session.flush()
    # Загруженный документ закрывает сигнал «нет документа» на этом этапе.
    await recompute_signals(session, [interaction.id], now)
    # Ключ файла в хранилище уходит получателям в документе обмена.
    await mark_changed(session, [interaction.id], "attachment")
    await session.commit()
    return attachment


async def list_attachments(
    session: AsyncSession, user: CurrentUser, interaction_id: uuid.UUID
) -> list[Attachment]:
    await visible_interaction(session, user, interaction_id)
    attachments = await session.scalars(
        select(Attachment)
        .where(Attachment.interaction_id == interaction_id)
        .order_by(Attachment.uploaded_at.desc(), Attachment.id)
    )
    return list(attachments)


async def find_attachment(
    session: AsyncSession, user: CurrentUser, attachment_id: uuid.UUID
) -> Attachment:
    """Вложение в области видимости пользователя; чужое — 404 (ADR-007)."""
    attachment = await session.scalar(
        apply_interaction_scope(
            select(Attachment)
            .join(Interaction, Interaction.id == Attachment.interaction_id)
            .where(Attachment.id == attachment_id),
            user,
        )
    )
    if attachment is None:
        raise AppError(ErrorCode.NOT_FOUND, ATTACHMENT_NOT_FOUND)
    return attachment


async def open_file(attachment: Attachment, storage: Storage | None = None) -> BinaryIO:
    storage = storage or get_storage()
    try:
        stream: BinaryIO = await run_in_threadpool(storage.open, attachment.storage_key)
    except OSError as error:
        raise AppError(ErrorCode.NOT_FOUND, ATTACHMENT_NOT_FOUND) from error
    return stream


def read_chunks(stream: BinaryIO) -> Iterator[bytes]:
    with stream:
        while chunk := stream.read(CHUNK_BYTES):
            yield chunk
