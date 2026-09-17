"""Импорт xls/xlsx: разбор файла, предпросмотр по соответствию колонок и применение."""

import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import AppError, ErrorCode, FieldError
from app.core.events import IMPORT_APPLIED, get_event_bus
from app.core.security import CurrentUser
from app.modules.attachments import files
from app.modules.audit.models import AuditLog
from app.modules.catalogs.models import (
    AppUser,
    ContactPerson,
    Product,
    ProgramProduct,
    University,
    Vendor,
)
from app.modules.imports import mapping, reader
from app.modules.imports.models import ImportBatch, ImportProfile, ImportRow
from app.modules.imports.schemas import ApplyResult
from app.modules.interactions.models import Contract, Interaction, InteractionNote, Transition
from app.modules.radar.service import recompute_signals
from app.modules.workflow.defaults import universities_group
from app.modules.workflow.service import GroupProcess, group_process

PREVIEW_ROWS = 20
BATCH_NOT_FOUND = "Загрузка не найдена."


@dataclass(slots=True)
class RowValues:
    university: str
    vendor: str
    product: str
    contract_number: str
    license_signed_at: date | None
    license_valid_until: date | None
    transfer_status: str
    manager: str
    contacts: str
    comment: str


def row_values(raw: dict[str, str], column_map: dict[str, str]) -> RowValues:
    def value(field: mapping.ImportField) -> str:
        header = column_map.get(field.value)
        return (raw.get(header) or "").strip() if header else ""

    return RowValues(
        university=value(mapping.ImportField.UNIVERSITY),
        vendor=value(mapping.ImportField.VENDOR),
        product=value(mapping.ImportField.PRODUCT),
        contract_number=value(mapping.ImportField.CONTRACT_NUMBER),
        license_signed_at=reader.parse_date(value(mapping.ImportField.LICENSE_SIGNED_AT)),
        license_valid_until=reader.parse_date(value(mapping.ImportField.LICENSE_VALID_UNTIL)),
        transfer_status=value(mapping.ImportField.TRANSFER_STATUS),
        manager=value(mapping.ImportField.MANAGER),
        contacts=value(mapping.ImportField.UNIVERSITY_CONTACTS),
        comment=value(mapping.ImportField.COMMENT),
    )


@dataclass(slots=True)
class Catalog:
    """Справочники в нормализованном виде: по ним решается судьба каждой строки."""

    universities: dict[str, University]
    products: dict[tuple[str, str], Product]
    default_programs: dict[uuid.UUID, uuid.UUID]
    users: dict[str, AppUser]
    interactions: dict[tuple[uuid.UUID, uuid.UUID, uuid.UUID], Interaction]
    group_id: uuid.UUID


async def load_catalog(session: AsyncSession) -> Catalog:
    universities = {}
    for university in await session.scalars(select(University)):
        universities[mapping.normalize(university.name)] = university
        universities.setdefault(mapping.normalize(university.short_name), university)

    products: dict[tuple[str, str], Product] = {}
    rows = await session.execute(
        select(Product, Vendor).join(Vendor, Vendor.id == Product.vendor_id)
    )
    for product, vendor in rows.tuples():
        products[(mapping.normalize(vendor.name), mapping.normalize(product.name))] = product

    default_programs = {
        product_id: program_id
        for program_id, product_id in (
            await session.execute(
                select(ProgramProduct.program_id, ProgramProduct.product_id).where(
                    ProgramProduct.is_default.is_(True)
                )
            )
        ).tuples()
    }
    users = {
        mapping.normalize(user.full_name): user
        for user in await session.scalars(select(AppUser).where(AppUser.is_active.is_(True)))
    }
    # Выгрузка заказчика описывает работу с вузами, поэтому сравнивается только с записями вузов.
    interactions = {
        (i.university_id, i.program_id, i.product_id): i
        for i in await session.scalars(
            select(Interaction).where(
                Interaction.status != "cancelled",
                Interaction.university_id.is_not(None),
                Interaction.product_id.is_not(None),
            )
        )
        if i.university_id is not None and i.product_id is not None
    }
    group = await universities_group(session)
    return Catalog(universities, products, default_programs, users, interactions, group.id)


def resolve_row(values: RowValues, catalog: Catalog) -> tuple[str, str | None]:
    """Что произойдёт со строкой при применении. Порядок проверок — от самой грубой к тонкой."""
    if not (values.university and values.vendor and values.product):
        return "skip", "Не заполнены обязательные колонки: вуз, вендор или ПО."

    product = catalog.products.get(
        (mapping.normalize(values.vendor), mapping.normalize(values.product))
    )
    if product is None:
        return "needs_program", f"ПО «{values.product}» нет в каталоге: выберите программу."
    program_id = catalog.default_programs.get(product.id)
    if program_id is None:
        return "needs_program", f"У ПО «{values.product}» нет программы по умолчанию."
    if values.manager and mapping.normalize(values.manager) not in catalog.users:
        return "conflict", f"Менеджер «{values.manager}» не найден среди пользователей."

    university = catalog.universities.get(mapping.normalize(values.university))
    if university is None:
        return "new", None
    if (university.id, program_id, product.id) in catalog.interactions:
        return "update", None
    return "new", None


async def _batch(session: AsyncSession, batch_id: uuid.UUID) -> ImportBatch:
    batch = await session.get(ImportBatch, batch_id)
    if batch is None:
        raise AppError(ErrorCode.NOT_FOUND, BATCH_NOT_FOUND)
    return batch


async def batch_rows(session: AsyncSession, batch_id: uuid.UUID) -> list[ImportRow]:
    rows = await session.scalars(
        select(ImportRow).where(ImportRow.batch_id == batch_id).order_by(ImportRow.row_no)
    )
    return list(rows)


async def create_batch(
    session: AsyncSession,
    user: CurrentUser,
    upload: UploadFile,
    settings: Settings | None = None,
) -> ImportBatch:
    settings = settings or get_settings()
    file_name = files.safe_name(upload.filename or "")
    kind = reader.file_kind(file_name)
    if kind is None:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Поддерживаются только файлы xls и xlsx.",
            errors=[FieldError(field="file", message="Нужен файл xls или xlsx")],
        )
    content = await upload.read()
    if len(content) > settings.max_upload_bytes:
        raise AppError(ErrorCode.FILE_TOO_LARGE, f"Файл больше {settings.max_upload_mb} МБ.")
    if files.match(file_name, content[: files.SIGNATURE_BYTES]) is None:
        raise AppError(ErrorCode.FILE_TYPE_NOT_ALLOWED, "Это не книга Excel.")
    try:
        sheet = reader.read(file_name, content)
    except reader.SheetError as error:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            str(error),
            errors=[FieldError(field="file", message="Файл не разобран")],
        ) from error
    if not sheet.rows:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "В файле нет строк с данными.",
            errors=[FieldError(field="file", message="Пустая таблица")],
        )

    batch = ImportBatch(
        file_name=file_name,
        file_kind=kind,
        status="uploaded",
        headers=sheet.headers,
        column_map={},
        stats={"total": len(sheet.rows)},
        uploaded_by=user.id,
    )
    session.add(batch)
    await session.flush()
    for row_no, raw in enumerate(sheet.rows, start=1):
        session.add(ImportRow(batch_id=batch.id, row_no=row_no, raw=raw, resolution="new"))
    await session.commit()
    return batch


async def set_mapping(
    session: AsyncSession,
    user: CurrentUser,
    batch_id: uuid.UUID,
    column_map: dict[str, str],
    save_as_profile: str | None = None,
) -> ImportBatch:
    batch = await _batch(session, batch_id)
    if batch.status == "applied":
        raise AppError(ErrorCode.VALIDATION_ERROR, "Загрузка уже применена.")

    missing = mapping.missing_required(column_map)
    if missing:
        raise AppError(
            ErrorCode.IMPORT_MAPPING_INVALID,
            f"Не сопоставлены обязательные поля: {', '.join(missing)}.",
            errors=[
                FieldError(field=f"column_map.{field}", message="Обязательное поле")
                for field in missing
            ],
        )
    unknown = sorted({header for header in column_map.values() if header not in batch.headers})
    if unknown:
        raise AppError(
            ErrorCode.IMPORT_MAPPING_INVALID,
            f"В файле нет колонок: {', '.join(unknown)}.",
        )

    catalog = await load_catalog(session)
    counter: Counter[str] = Counter()
    for row in await batch_rows(session, batch_id):
        row.resolution, row.detail = resolve_row(row_values(row.raw, column_map), catalog)
        counter[row.resolution] += 1

    batch.column_map = column_map
    batch.status = "previewed"
    batch.stats = {"total": sum(counter.values()), **counter}
    if save_as_profile:
        await _save_profile(session, save_as_profile, batch)
    await session.commit()
    return batch


async def _save_profile(session: AsyncSession, name: str, batch: ImportBatch) -> None:
    profile = await session.scalar(select(ImportProfile).where(ImportProfile.name == name))
    if profile is None:
        profile = ImportProfile(name=name, file_kind=batch.file_kind, column_map=batch.column_map)
        session.add(profile)
        await session.flush()
    else:
        profile.file_kind = batch.file_kind
        profile.column_map = batch.column_map
    batch.profile_id = profile.id


async def list_profiles(session: AsyncSession) -> list[ImportProfile]:
    profiles = await session.scalars(select(ImportProfile).order_by(ImportProfile.name))
    return list(profiles)


def _short_name(name: str) -> str:
    """Сокращение вуза: аббревиатура из заглавных букв, иначе первое слово."""
    letters = "".join(ch for ch in name if ch.isupper())
    if 2 <= len(letters) <= 12:
        return letters
    return name.split(",")[0].split()[0][:60] if name.split() else name[:60]


async def _university(session: AsyncSession, catalog: Catalog, name: str) -> University:
    key = mapping.normalize(name)
    university = catalog.universities.get(key)
    if university is None:
        university = University(name=name[:300], short_name=_short_name(name), region="Не указан")
        session.add(university)
        await session.flush()
        catalog.universities[key] = university
    return university


async def _contract(
    session: AsyncSession, university_id: uuid.UUID, values: RowValues
) -> Contract | None:
    if not values.contract_number:
        return None
    contract = await session.scalar(
        select(Contract).where(
            Contract.university_id == university_id, Contract.number == values.contract_number[:60]
        )
    )
    if contract is None:
        contract = Contract(university_id=university_id, number=values.contract_number[:60])
        session.add(contract)
    contract.signed_at = values.license_signed_at or contract.signed_at
    contract.license_signed_at = values.license_signed_at or contract.license_signed_at
    contract.license_valid_until = values.license_valid_until or contract.license_valid_until
    contract.transfer_status = values.transfer_status[:120] or contract.transfer_status
    await session.flush()
    return contract


async def apply_batch(
    session: AsyncSession,
    user: CurrentUser,
    batch_id: uuid.UUID,
    trace_id: str | None = None,
    now: datetime | None = None,
) -> ApplyResult:
    now = now or datetime.now(UTC)
    batch = await _batch(session, batch_id)
    if batch.status != "previewed":
        raise AppError(
            ErrorCode.VALIDATION_ERROR, "Сначала задайте соответствие колонок и посмотрите итог."
        )

    process = await group_process(session, await universities_group(session))
    catalog = await load_catalog(session)
    counter: Counter[str] = Counter()
    touched: list[uuid.UUID] = []

    for row in await batch_rows(session, batch_id):
        if row.resolution not in {"new", "update"}:
            counter[row.resolution] += 1
            continue
        values = row_values(row.raw, batch.column_map)
        interaction, created = await _apply_row(session, user, catalog, process, values, now)
        counter["created" if created else "updated"] += 1
        touched.append(interaction.id)

    await session.flush()
    await recompute_signals(session, touched, now)
    batch.status = "applied"
    batch.applied_at = now
    batch.stats = {**batch.stats, **counter}
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="import.applied",
            entity_kind="import_batch",
            entity_id=batch.id,
            after=dict(counter),
            trace_id=trace_id,
        )
    )
    await session.commit()
    await get_event_bus().publish(IMPORT_APPLIED, {"batch_id": str(batch.id), **dict(counter)})
    return ApplyResult(
        batch_id=batch.id,
        created=counter["created"],
        updated=counter["updated"],
        skipped=counter["skip"],
        conflicts=counter["conflict"],
        needs_program=counter["needs_program"],
    )


async def _apply_row(
    session: AsyncSession,
    user: CurrentUser,
    catalog: Catalog,
    process: GroupProcess,
    values: RowValues,
    now: datetime,
) -> tuple[Interaction, bool]:
    university = await _university(session, catalog, values.university)
    product = catalog.products[
        (mapping.normalize(values.vendor), mapping.normalize(values.product))
    ]
    program_id = catalog.default_programs[product.id]
    contract = await _contract(session, university.id, values)
    owner = catalog.users.get(mapping.normalize(values.manager)) if values.manager else None
    owner_id = owner.id if owner else user.id

    key = (university.id, program_id, product.id)
    interaction = catalog.interactions.get(key)
    if interaction is not None:
        # Этап не откатываем: файл описывает договор, а процесс ведёт КАМ в карточке.
        interaction.contract_id = contract.id if contract else interaction.contract_id
        interaction.owner_user_id = owner_id
        interaction.last_activity_at = now
        interaction.version += 1
        return interaction, False

    # Статус из файла ведёт на этап базового процесса; если его в схеме нет — на первый этап.
    stage = process.stages.get(
        mapping.stage_for_status(values.transfer_status) or "", process.start
    )
    entered_at = (
        datetime.combine(values.license_signed_at, datetime.min.time(), tzinfo=UTC)
        if values.license_signed_at
        else now
    )
    interaction = Interaction(
        group_id=catalog.group_id,
        university_id=university.id,
        program_id=program_id,
        product_id=product.id,
        contract_id=contract.id if contract else None,
        workflow_version_id=process.version.id,
        current_stage_id=stage.id,
        stage_entered_at=entered_at,
        owner_user_id=owner_id,
        source="import",
        last_activity_at=entered_at,
    )
    session.add(interaction)
    await session.flush()
    session.add(
        Transition(
            interaction_id=interaction.id,
            from_stage_id=None,
            to_stage_id=stage.id,
            occurred_at=entered_at,
            actor_user_id=user.id,
            comment="Загружено из файла",
            source="import",
        )
    )
    if values.comment:
        session.add(
            InteractionNote(
                interaction_id=interaction.id, author_user_id=user.id, text=values.comment
            )
        )
    if values.contacts:
        session.add(ContactPerson(university_id=university.id, full_name=values.contacts[:200]))
    catalog.interactions[key] = interaction
    return interaction, True
