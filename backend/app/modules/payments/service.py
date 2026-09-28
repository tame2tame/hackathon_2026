"""Оплаты частных лиц: выгрузка платёжной системы → клиент, запись B2C и зачисление в LMS.

Кейсодержатель присылает оплаты массивом JSON: номер заявки, курс, ФИО, телефон, почта и номер
потока. Оплата — ровно то событие, после которого запись частного лица уходит с этапа «Оплата»
на «Зачисление в LMS», поэтому загрузка делает это сама: находит человека по отпечатку почты
(или заводит карточку), находит его запись по курсу (или заводит её) и переводит на зачисление.
Номер заявки и поток остаются в истории записи и в таблице оплат, а подтверждением оплаты служит
сама выгрузка платёжной системы — документ к переходу не прикладывается.

Как и остальные загрузки, работает построчно: одна кривая запись не отменяет файл, а
по умолчанию всё только показывается (`dry_run`).
"""

import json
import re
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import crypto
from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode, FieldError
from app.core.scope import apply_interaction_scope
from app.core.security import CurrentUser
from app.modules.audit.models import AuditLog
from app.modules.catalogs.models import CounterpartyGroup, Program, ProgramProduct
from app.modules.clients.models import Client
from app.modules.imports import files, reader
from app.modules.imports.files import FieldSpec, ImportOutcome, RowError, RowResult
from app.modules.imports.mapping import normalize
from app.modules.integrations.outbox import mark_changed
from app.modules.interactions.models import Interaction, Transition
from app.modules.payments.models import Payment
from app.modules.radar.service import recompute_signals
from app.modules.workflow.defaults import INDIVIDUALS_GROUP
from app.modules.workflow.models import Stage
from app.modules.workflow.service import GroupProcess, group_process

ENROLLMENT = "enrollment"
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

SPECS: tuple[FieldSpec, ...] = (
    FieldSpec("order_no", "Номер заявки", True, aliases=("Заявка", "Номер заказа")),
    FieldSpec("course", "Курс", True, aliases=("Программа",)),
    FieldSpec("last_name", "Фамилия", True),
    FieldSpec("first_name", "Имя", True),
    FieldSpec("middle_name", "Отчество", aliases=("Отчество (при наличии)",)),
    FieldSpec("phone", "Телефон", aliases=("Номер телефона",)),
    FieldSpec("email", "Email", True, aliases=("Почта", "E-mail")),
    FieldSpec("stream", "Номер потока", aliases=("Поток",)),
)


def phone_of(value: str) -> str | None:
    """«7 (999) 023-43-65», «89990234365» и «79990234365» — один номер: +7 (999) 023-43-65."""
    if not value.strip():
        return None
    digits = re.sub(r"\D", "", value)
    if len(digits) == 10:
        digits = "7" + digits
    if len(digits) != 11 or digits[0] not in "78":
        raise RowError(f"Телефон не распознан: «{value}»")
    return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"


def _stream(value: str) -> int | None:
    if not value.strip():
        return None
    try:
        stream = int(float(value))
    except ValueError as error:
        raise RowError(f"Номер потока — число, а не «{value}»") from error
    if stream < 1:
        raise RowError("Номер потока — число от 1")
    return stream


def _records(file_name: str, content: bytes, encoding: str | None) -> list[dict[str, Any] | None]:
    """Записи файла. В JSON платёжной системы бывает `null` среди записей — это строка с ошибкой,
    а не повод отвергнуть весь файл."""
    if not file_name.lower().endswith(".json"):
        return list(files.records(file_name, content, encoding, "Файл оплат"))
    try:
        data = json.loads(content.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError) as error:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Файл JSON не разобран: нужен массив оплат или объект с полем items.",
            errors=[FieldError(field="file", message="Некорректный JSON")],
        ) from error
    items = data.get("items") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "В JSON нужен массив оплат или объект с полем items.",
            errors=[FieldError(field="file", message="Нет списка записей")],
        )
    if len(items) > reader.MAX_ROWS:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            f"В файле больше {reader.MAX_ROWS} записей. Разбейте его на части.",
            errors=[FieldError(field="file", message="Слишком много записей")],
        )
    return [item if isinstance(item, dict) else None for item in items]


class _Catalog:
    """Справочники на одну загрузку: курсы по названию и процесс группы частных лиц."""

    def __init__(
        self,
        programs: dict[str, Program],
        products: dict[uuid.UUID, list[tuple[uuid.UUID, bool]]],
        group: CounterpartyGroup,
        process: GroupProcess,
    ) -> None:
        self.programs = programs
        self.products = products
        self.group = group
        self.process = process

    @classmethod
    async def load(cls, session: AsyncSession) -> "_Catalog":
        group = await session.scalar(
            select(CounterpartyGroup).where(CounterpartyGroup.code == INDIVIDUALS_GROUP)
        )
        if group is None:
            raise AppError(ErrorCode.NOT_FOUND, "Группа частных лиц не заведена.")
        process = await group_process(session, group)
        if ENROLLMENT not in process.stages:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "В процессе частных лиц нет этапа «Зачисление в LMS»: оплату некуда провести.",
            )
        products: dict[uuid.UUID, list[tuple[uuid.UUID, bool]]] = {}
        for link in await session.scalars(select(ProgramProduct)):
            products.setdefault(link.program_id, []).append((link.product_id, link.is_default))
        programs = {
            normalize(program.name): program
            for program in await session.scalars(
                select(Program).where(Program.archived_at.is_(None))
            )
        }
        return cls(programs, products, group, process)

    def program(self, course: str) -> tuple[Program, uuid.UUID | None]:
        program = self.programs.get(normalize(course))
        if program is None:
            raise RowError(f"Курса «{course}» нет в справочнике программ")
        links = self.products.get(program.id, [])
        # Продукт курса: основная пара, а если продукт у курса один — он.
        product_id = next((product for product, is_default in links if is_default), None)
        if product_id is None and len(links) == 1:
            product_id = links[0][0]
        if links and product_id is None:
            raise RowError(f"У курса «{course}» несколько продуктов и основной не выбран")
        return program, product_id


async def _client(
    session: AsyncSession, user: CurrentUser, values: dict[str, str], phone: str | None
) -> tuple[Client, bool]:
    email = values["email"]
    fingerprint = crypto.fingerprint(email)
    name = " ".join(
        part
        for part in (values["last_name"], values["first_name"], values.get("middle_name"))
        if part
    )
    client = await session.scalar(
        select(Client).where(
            Client.kind == "person", Client.email_fp == fingerprint, Client.archived_at.is_(None)
        )
    )
    if client is None:
        # Карточки, заведённые до появления отпечатка: сверяем почту у тёзок напрямую.
        for candidate in await session.scalars(
            select(Client).where(
                Client.kind == "person",
                Client.email_fp.is_(None),
                Client.archived_at.is_(None),
                Client.name == name,
            )
        ):
            if (crypto.decrypt(candidate.email_enc) or "").casefold() == email.casefold():
                candidate.email_fp = fingerprint
                client = candidate
                break
    if client is not None:
        if phone and client.phone_enc is None:
            client.phone_enc = crypto.encrypt(phone)
        return client, False
    client = Client(
        kind="person",
        name=name[:300],
        email_enc=crypto.encrypt(email),
        email_fp=fingerprint,
        phone_enc=crypto.encrypt(phone),
        created_by=user.id,
    )
    session.add(client)
    await session.flush()
    return client, True


def _order(process: GroupProcess) -> list[str]:
    return [stage.code for stage in sorted(process.stages.values(), key=lambda item: item.position)]


async def _apply_row(
    session: AsyncSession,
    user: CurrentUser,
    catalog: _Catalog,
    values: dict[str, str],
    now: datetime,
    trace_id: str | None,
) -> tuple[Literal["created", "updated", "unchanged"], str | None, uuid.UUID | None]:
    order_no = values["order_no"][:80]
    known = await session.scalar(select(Payment.id).where(Payment.order_no == order_no))
    if known is not None:
        return "unchanged", "оплата уже загружена", None
    email = values["email"]
    if not EMAIL.match(email):
        raise RowError(f"Это не почта: «{email}»")
    phone = phone_of(values.get("phone", ""))
    stream = _stream(values.get("stream", ""))
    program, product_id = catalog.program(values["course"])
    client, new_client = await _client(session, user, values, phone)
    enrollment = catalog.process.stages[ENROLLMENT]
    comment = f"Оплата по заявке {order_no}" + (f", поток {stream}" if stream else "")

    interaction = await session.scalar(
        select(Interaction)
        .where(
            Interaction.client_id == client.id,
            Interaction.program_id == program.id,
            Interaction.product_id.is_not_distinct_from(product_id),
            Interaction.status != "cancelled",
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    action: Literal["created", "updated"]
    if interaction is None:
        interaction = Interaction(
            group_id=catalog.group.id,
            client_id=client.id,
            program_id=program.id,
            product_id=product_id,
            workflow_version_id=catalog.process.version.id,
            current_stage_id=enrollment.id,
            stage_entered_at=now,
            owner_user_id=user.id,
            source="import",
            last_activity_at=now,
        )
        session.add(interaction)
        await session.flush()
        session.add(
            Transition(
                interaction_id=interaction.id,
                from_stage_id=None,
                to_stage_id=enrollment.id,
                occurred_at=now,
                actor_user_id=user.id,
                comment=comment,
                source="import",
            )
        )
        action, detail = "created", "новый клиент и запись" if new_client else "новая запись"
    else:
        current = await session.get(Stage, interaction.current_stage_id)
        order = _order(catalog.process)
        position = order.index(current.code) if current and current.code in order else -1
        if interaction.status == "paused":
            raise RowError("Запись клиента приостановлена: оплату проведите в карточке")
        if interaction.status == "completed":
            action, detail = "updated", "запись уже завершена, этап не меняется"
        elif position < order.index(ENROLLMENT):
            session.add(
                Transition(
                    interaction_id=interaction.id,
                    from_stage_id=interaction.current_stage_id,
                    to_stage_id=enrollment.id,
                    occurred_at=now,
                    actor_user_id=user.id,
                    comment=comment,
                    source="import",
                )
            )
            interaction.current_stage_id = enrollment.id
            interaction.stage_entered_at = now
            interaction.version += 1
            action, detail = "updated", "переведена на «Зачисление в LMS»"
        else:
            action = "updated"
            detail = f"этап не меняется: «{current.name if current else '—'}»"
        interaction.last_activity_at = now

    visible = await session.scalar(
        apply_interaction_scope(
            select(Interaction.id).where(Interaction.id == interaction.id), user
        )
    )
    if visible is None:
        raise RowError("Запись клиента вне вашей области видимости")
    session.add(
        Payment(
            order_no=order_no,
            interaction_id=interaction.id,
            client_id=client.id,
            program_id=program.id,
            stream_no=stream,
            imported_by=user.id,
        )
    )
    # В журнал — номер заявки и поток, но не ФИО и не почта.
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="payment.imported",
            entity_kind="interaction",
            entity_id=interaction.id,
            after={"order_no": order_no, "stream": stream, "program_id": str(program.id)},
            trace_id=trace_id,
        )
    )
    return action, detail, interaction.id


async def import_payments(
    session: AsyncSession,
    user: CurrentUser,
    upload: UploadFile,
    dry_run: bool,
    encoding: str | None = None,
    trace_id: str | None = None,
    now: datetime | None = None,
) -> ImportOutcome:
    now = now or datetime.now(UTC)
    content = await upload.read()
    settings = get_settings()
    if len(content) > settings.max_upload_bytes:
        raise AppError(ErrorCode.FILE_TOO_LARGE, f"Файл больше {settings.max_upload_mb} МБ.")
    if not crypto.is_configured():
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Не настроен ключ шифрования: карточки клиентов с почтой сохранить нельзя.",
            errors=[FieldError(field="file", message="Шифрование не настроено")],
        )
    rows = _records(upload.filename or "", content, encoding)
    files.check_columns(SPECS, [row for row in rows if row is not None])

    outcome = ImportOutcome(kind="payments", dry_run=dry_run)
    touched: list[uuid.UUID] = []
    seen: set[str] = set()
    savepoint = await session.begin_nested()
    catalog = await _Catalog.load(session)
    for row_no, raw in enumerate(rows, start=1):
        if raw is None:
            outcome.rows.append(RowResult(row_no, "", "error", "Пустая запись"))
            continue
        values = files.normalized(SPECS, raw)
        missing = [spec.label for spec in SPECS if spec.required and not values.get(spec.name)]
        if missing:
            outcome.rows.append(
                RowResult(
                    row_no,
                    values.get("order_no", ""),
                    "error",
                    f"Не заполнено: {', '.join(missing)}",
                )
            )
            continue
        key = values["order_no"]
        if key in seen:
            outcome.rows.append(RowResult(row_no, key, "error", "Та же заявка уже есть выше"))
            continue
        seen.add(key)
        try:
            async with session.begin_nested():
                action, detail, interaction_id = await _apply_row(
                    session, user, catalog, values, now, trace_id
                )
                await session.flush()
        except RowError as error:
            outcome.rows.append(RowResult(row_no, key, "error", str(error)))
        except IntegrityError:
            # Запись этого клиента по курсу завели параллельно: строку повторят позже.
            outcome.rows.append(
                RowResult(row_no, key, "error", "Запись изменилась во время загрузки: повторите")
            )
        else:
            outcome.rows.append(RowResult(row_no, key, action, detail))
            if interaction_id is not None:
                touched.append(interaction_id)

    if dry_run:
        await savepoint.rollback()
        return outcome
    if touched:
        await recompute_signals(session, touched, now)
        await mark_changed(session, touched, "payment")
    await savepoint.commit()
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="payment.file_imported",
            entity_kind="payment",
            after={
                "file": (upload.filename or "")[:200],
                "created": outcome.count("created"),
                "updated": outcome.count("updated"),
                "unchanged": outcome.count("unchanged"),
                "errors": outcome.count("error"),
            },
            trace_id=trace_id,
        )
    )
    await session.commit()
    return outcome
