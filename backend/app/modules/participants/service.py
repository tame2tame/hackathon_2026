"""Списки обучающихся и преподавателей: ведение вручную, файлом и выгрузка.

Кто видит запись, тот видит и её списки: область видимости проверяется по самой записи
(ADR-007). ФИО показывается в списке, а почта целиком — только по отдельному запросу, и каждый
такой запрос вместе с выгрузкой файла пишется в аудит: это персональные данные.
"""

import json
import re
import uuid
from datetime import UTC, datetime
from typing import Any, Literal, cast

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import crypto
from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode, FieldError
from app.core.scope import visible_interaction
from app.core.security import CurrentUser
from app.modules.audit.models import AuditLog
from app.modules.imports import files
from app.modules.imports.files import EXPORT_TYPES, FieldSpec, ImportOutcome, RowError, RowResult
from app.modules.imports.mapping import normalize
from app.modules.participants.models import Participant
from app.modules.participants.schemas import (
    EMAIL_PATTERN,
    ROLE_NAMES,
    ParticipantContactOut,
    ParticipantCountsOut,
    ParticipantCreate,
    ParticipantOut,
    ParticipantRole,
    ParticipantsOut,
)
from app.modules.reports import renderers

NOT_FOUND = "Участник не найден или недоступен."
SPECS: tuple[FieldSpec, ...] = (
    FieldSpec("full_name", "ФИО", True, aliases=("Фамилия Имя Отчество", "Участник", "Слушатель")),
    FieldSpec("email", "Email", aliases=("Почта", "E-mail", "Электронная почта")),
    FieldSpec("role", "Роль", aliases=("Кто",)),
    FieldSpec("external_ref", "Идентификатор в LMS", aliases=("ID в LMS", "Внешний код")),
)
ROLE_WORDS = {
    "обучающийся": "student",
    "обучающаяся": "student",
    "студент": "student",
    "слушатель": "student",
    "student": "student",
    "преподаватель": "teacher",
    "преподавательница": "teacher",
    "учитель": "teacher",
    "teacher": "teacher",
}


def _out(participant: Participant) -> ParticipantOut:
    return ParticipantOut(
        id=participant.id,
        role=cast(ParticipantRole, participant.role),
        full_name=participant.full_name,
        email=crypto.mask_email(crypto.decrypt(participant.email_enc)),
        has_email=participant.email_enc is not None,
        source=participant.source,
        created_at=participant.created_at,
    )


async def list_participants(
    session: AsyncSession, user: CurrentUser, interaction_id: uuid.UUID, role: str | None = None
) -> ParticipantsOut:
    await visible_interaction(session, user, interaction_id)
    stmt = (
        select(Participant)
        .where(Participant.interaction_id == interaction_id, Participant.archived_at.is_(None))
        .order_by(Participant.role, Participant.full_name)
    )
    if role:
        stmt = stmt.where(Participant.role == role)
    items = [_out(participant) for participant in await session.scalars(stmt)]
    totals = await session.execute(
        select(Participant.role, func.count())
        .where(Participant.interaction_id == interaction_id, Participant.archived_at.is_(None))
        .group_by(Participant.role)
    )
    counts = {role: total for role, total in totals.all()}
    return ParticipantsOut(
        counts=ParticipantCountsOut(
            students=counts.get("student", 0), teachers=counts.get("teacher", 0)
        ),
        items=items,
    )


async def _find(session: AsyncSession, user: CurrentUser, participant_id: uuid.UUID) -> Participant:
    participant = await session.get(Participant, participant_id)
    if participant is None or participant.archived_at is not None:
        raise AppError(ErrorCode.NOT_FOUND, NOT_FOUND)
    # Права на участника — это права на его запись.
    await visible_interaction(session, user, participant.interaction_id)
    return participant


def _require_key(email: str | None) -> None:
    if email and not crypto.is_configured():
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Не настроен ключ шифрования: список с почтой сохранить нельзя.",
            errors=[FieldError(field="email", message="Шифрование не настроено")],
        )


async def add_participant(
    session: AsyncSession,
    user: CurrentUser,
    interaction_id: uuid.UUID,
    payload: ParticipantCreate,
    trace_id: str | None = None,
) -> ParticipantOut:
    await visible_interaction(session, user, interaction_id)
    email = str(payload.email) if payload.email else None
    _require_key(email)
    fingerprint = crypto.fingerprint(email)
    name = payload.full_name.strip()
    await _check_free(session, interaction_id, fingerprint, payload.role, name)
    participant = Participant(
        interaction_id=interaction_id,
        role=payload.role,
        full_name=name,
        email_enc=crypto.encrypt(email),
        email_fp=fingerprint,
        external_ref=payload.external_ref,
        source="manual",
        created_by=user.id,
    )
    session.add(participant)
    try:
        # Двойной клик обходит проверку выше: последнее слово за уникальным индексом.
        async with session.begin_nested():
            await session.flush()
    except IntegrityError as error:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Человек с этой почтой уже есть в списке записи.",
            errors=[FieldError(field="email", message="Почта уже в списке")],
        ) from error
    # В журнал идёт факт, но не персональные данные.
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="participant.added",
            entity_kind="participant",
            entity_id=participant.id,
            after={"role": participant.role, "has_email": email is not None},
            trace_id=trace_id,
        )
    )
    await session.commit()
    return _out(participant)


async def _check_free(
    session: AsyncSession,
    interaction_id: uuid.UUID,
    fingerprint: str | None,
    role: str,
    full_name: str,
) -> None:
    """Один человек в списке записи один раз: по почте, а без почты — по ФИО и роли."""
    if fingerprint is not None:
        taken = await session.scalar(
            select(Participant.id).where(
                Participant.interaction_id == interaction_id,
                Participant.email_fp == fingerprint,
            )
        )
        if taken is not None:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Человек с этой почтой уже есть в списке записи.",
                errors=[FieldError(field="email", message="Почта уже в списке")],
            )
        return
    same_name = await session.scalars(
        select(Participant.full_name).where(
            Participant.interaction_id == interaction_id,
            Participant.role == role,
            Participant.archived_at.is_(None),
        )
    )
    if normalize(full_name) in {normalize(item) for item in same_name}:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Человек с таким ФИО уже есть в списке записи.",
            errors=[FieldError(field="full_name", message="Уже в списке")],
        )


async def get_contact(
    session: AsyncSession, user: CurrentUser, participant_id: uuid.UUID, trace_id: str | None = None
) -> ParticipantContactOut:
    """Почта целиком: показывается по запросу, и запрос остаётся в аудите."""
    participant = await _find(session, user, participant_id)
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="participant.contact_viewed",
            entity_kind="participant",
            entity_id=participant.id,
            after={"role": participant.role},
            trace_id=trace_id,
        )
    )
    await session.commit()
    return ParticipantContactOut(
        id=participant.id,
        full_name=participant.full_name,
        email=crypto.decrypt(participant.email_enc),
    )


async def remove_participant(
    session: AsyncSession, user: CurrentUser, participant_id: uuid.UUID, trace_id: str | None = None
) -> None:
    """Человек ушёл с обучения: строка со списка снимается, персональные данные стираются."""
    participant = await _find(session, user, participant_id)
    participant.archived_at = datetime.now(UTC)
    participant.email_enc = None
    participant.email_fp = None
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="participant.removed",
            entity_kind="participant",
            entity_id=participant.id,
            before={"role": participant.role},
            trace_id=trace_id,
        )
    )
    await session.commit()


def _role_of(value: str, default: ParticipantRole) -> str:
    if not value.strip():
        return default
    role = ROLE_WORDS.get(normalize(value))
    if role is None:
        raise RowError(f"Не понятно, обучающийся или преподаватель: «{value}»")
    return role


async def import_participants(
    session: AsyncSession,
    user: CurrentUser,
    interaction_id: uuid.UUID,
    upload: UploadFile,
    dry_run: bool,
    role: ParticipantRole = "student",
    encoding: str | None = None,
    trace_id: str | None = None,
) -> ImportOutcome:
    """Список файлом: строка находит человека по почте, а без почты — по ФИО и роли."""
    await visible_interaction(session, user, interaction_id)
    content = await upload.read()
    settings = get_settings()
    if len(content) > settings.max_upload_bytes:
        raise AppError(ErrorCode.FILE_TOO_LARGE, f"Файл больше {settings.max_upload_mb} МБ.")
    rows = files.records(upload.filename or "", content, encoding, "Список")
    files.check_columns(SPECS, rows)

    outcome = ImportOutcome(kind="participants", dry_run=dry_run)
    savepoint = await session.begin_nested()
    existing = {
        (item.email_fp or f"{item.role}:{normalize(item.full_name)}"): item
        for item in await session.scalars(
            select(Participant).where(
                Participant.interaction_id == interaction_id, Participant.archived_at.is_(None)
            )
        )
    }
    seen: set[str] = set()
    for row_no, raw in enumerate(rows, start=1):
        values = files.normalized(SPECS, raw)
        name = values.get("full_name", "")
        if not name:
            outcome.rows.append(RowResult(row_no, "", "error", "Не заполнено: ФИО"))
            continue
        try:
            async with session.begin_nested():
                action, detail = await _apply_row(
                    session, user, interaction_id, values, role, existing, seen
                )
                await session.flush()
        except RowError as error:
            outcome.rows.append(RowResult(row_no, name, "error", str(error)))
        except IntegrityError:
            # Строка упёрлась в ограничение базы: остальные строки файла не виноваты.
            outcome.rows.append(RowResult(row_no, name, "error", "Такой человек уже есть в списке"))
        else:
            outcome.rows.append(RowResult(row_no, name, action, detail))

    if dry_run:
        await savepoint.rollback()
        return outcome
    await savepoint.commit()
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="participant.imported",
            entity_kind="interaction",
            entity_id=interaction_id,
            after={
                "file": (upload.filename or "")[:200],
                "created": outcome.count("created"),
                "updated": outcome.count("updated"),
                "errors": outcome.count("error"),
            },
            trace_id=trace_id,
        )
    )
    await session.commit()
    return outcome


async def _apply_row(
    session: AsyncSession,
    user: CurrentUser,
    interaction_id: uuid.UUID,
    values: dict[str, str],
    default_role: ParticipantRole,
    existing: dict[str, Participant],
    seen: set[str],
) -> tuple[Literal["created", "updated", "unchanged"], str | None]:
    name = values["full_name"][:300]
    email = values.get("email") or None
    if email and not re.match(EMAIL_PATTERN, email):
        raise RowError(f"Это не почта: «{email}»")
    _require_key(email)
    role = _role_of(values.get("role", ""), default_role)
    fingerprint = crypto.fingerprint(email)
    by_name = f"{role}:{normalize(name)}"
    key = fingerprint or by_name
    if key in seen or (fingerprint is not None and by_name in seen):
        raise RowError("Тот же человек уже есть выше в файле")
    seen.add(key)

    # Человека, заведённого раньше без почты, ищем по ФИО и роли: иначе список с адресами
    # из LMS завёл бы вторую строку на того же слушателя.
    participant = existing.get(key) or (existing.get(by_name) if fingerprint else None)
    if participant is None:
        participant = Participant(
            interaction_id=interaction_id,
            role=role,
            full_name=name,
            email_enc=crypto.encrypt(email),
            email_fp=fingerprint,
            external_ref=(values.get("external_ref") or "")[:120] or None,
            source="import",
            created_by=user.id,
        )
        session.add(participant)
        existing[key] = participant
        return "created", None

    changed: list[str] = []
    if participant.full_name != name:
        participant.full_name = name
        changed.append("ФИО")
    if participant.role != role:
        participant.role = role
        changed.append("роль")
    if email and participant.email_enc is None:
        participant.email_enc = crypto.encrypt(email)
        participant.email_fp = fingerprint
        existing[key] = participant
        changed.append("почта")
    external_ref = (values.get("external_ref") or "")[:120]
    if external_ref and participant.external_ref != external_ref:
        participant.external_ref = external_ref
        changed.append("идентификатор в LMS")
    if not changed:
        return "unchanged", None
    return "updated", "обновлено: " + ", ".join(changed)


async def export_participants(
    session: AsyncSession,
    user: CurrentUser,
    interaction_id: uuid.UUID,
    fmt: Literal["json", "csv", "xlsx"],
    encoding: Literal["utf-8", "windows-1251"] = "utf-8",
    trace_id: str | None = None,
) -> tuple[bytes, str, str]:
    """Список файлом в том же виде, в каком его принимает загрузка. Выгрузка пишется в аудит."""
    await visible_interaction(session, user, interaction_id)
    participants = list(
        await session.scalars(
            select(Participant)
            .where(Participant.interaction_id == interaction_id, Participant.archived_at.is_(None))
            .order_by(Participant.role, Participant.full_name)
        )
    )
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="participant.exported",
            entity_kind="interaction",
            entity_id=interaction_id,
            after={"format": fmt, "rows": len(participants)},
            trace_id=trace_id,
        )
    )
    await session.commit()

    rows: list[dict[str, str]] = [
        {
            "full_name": participant.full_name,
            "email": crypto.decrypt(participant.email_enc) or "",
            "role": ROLE_NAMES[participant.role],
            "external_ref": participant.external_ref or "",
        }
        for participant in participants
    ]
    stamp = datetime.now(UTC).strftime("%Y-%m-%d")
    file_name = f"participants-{stamp}.{fmt}"
    if fmt == "json":
        items: list[dict[str, Any]] = [
            {spec.name: row[spec.name] for spec in SPECS} for row in rows
        ]
        content = json.dumps({"kind": "participants", "items": items}, ensure_ascii=False, indent=2)
        return content.encode("utf-8"), EXPORT_TYPES["json"], file_name
    headers = [spec.label for spec in SPECS]
    table = [[row[spec.name] for spec in SPECS] for row in rows]
    if fmt == "csv":
        media = f"{EXPORT_TYPES['csv']}; charset={encoding}"
        return renderers.render("csv", headers, table, "Участники", encoding), media, file_name
    return renderers.render("xlsx", headers, table, "Участники"), EXPORT_TYPES["xlsx"], file_name
