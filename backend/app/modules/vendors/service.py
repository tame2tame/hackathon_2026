"""Вендоры и их контакты: справочник с id и люди, которые отвечают за продукты."""

import re
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from typing import cast

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import crypto
from app.core.errors import AppError, ErrorCode, FieldError
from app.core.security import CurrentUser
from app.modules.audit.models import AuditLog
from app.modules.catalogs.models import Product, Vendor
from app.modules.imports.files import RowError
from app.modules.imports.mapping import normalize
from app.modules.vendors.models import CHANNELS, VendorContact, vendor_contact_product
from app.modules.vendors.schemas import (
    Channel,
    VendorContactCreate,
    VendorContactOut,
    VendorOut,
    VendorProductOut,
)

# «Почта, Чат в ТГ» → email и telegram. Ключи — слова без регистра, пробелов и знаков.
CHANNEL_WORDS = {
    "почта": "email",
    "email": "email",
    "емейл": "email",
    "электроннаяпочта": "email",
    "чатвтг": "telegram",
    "тг": "telegram",
    "telegram": "telegram",
    "телеграм": "telegram",
    "телеграмм": "telegram",
    "телефон": "phone",
    "звонок": "phone",
}
QUOTED = re.compile(r"[«\"“]([^»\"”]+)[»\"”]")


def product_names(cell: str) -> list[str]:
    """«RT.DataLake», «RT.Warehouse» → два продукта; без кавычек — через запятую."""
    quoted = [name.strip() for name in QUOTED.findall(cell) if name.strip()]
    if quoted:
        return quoted
    return [name.strip() for name in re.split(r"[,;]", cell) if name.strip()]


def channels_of(cell: str) -> list[str]:
    channels: list[str] = []
    for word in re.split(r"[,;/]", cell):
        if not word.strip():
            continue
        channel = CHANNEL_WORDS.get(normalize(word))
        if channel is None:
            raise RowError(f"Не понятный способ связи: «{word.strip()}»")
        if channel not in channels:
            channels.append(channel)
    return channels


def _require_key(email: str | None, phone: str | None) -> None:
    if (email or phone) and not crypto.is_configured():
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Не настроен ключ шифрования: контакт с персональными данными сохранить нельзя.",
            errors=[FieldError(field="email", message="Шифрование не настроено")],
        )


async def _products_of(
    session: AsyncSession, contact_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[VendorProductOut]]:
    rows = await session.execute(
        select(vendor_contact_product.c.contact_id, Product.id, Product.name)
        .join(Product, Product.id == vendor_contact_product.c.product_id)
        .where(vendor_contact_product.c.contact_id.in_(contact_ids))
        .order_by(Product.name)
    )
    products: dict[uuid.UUID, list[VendorProductOut]] = defaultdict(list)
    for contact_id, product_id, name in rows.tuples():
        products[contact_id].append(VendorProductOut(id=product_id, name=name))
    return products


def _contact_out(
    contact: VendorContact, products: list[VendorProductOut] | None = None
) -> VendorContactOut:
    return VendorContactOut(
        id=contact.id,
        vendor_id=contact.vendor_id,
        full_name=contact.full_name,
        email=crypto.decrypt(contact.email_enc),
        phone=crypto.decrypt(contact.phone_enc),
        channels=[cast(Channel, channel) for channel in contact.channels if channel in CHANNELS],
        products=products or [],
        archived_at=contact.archived_at,
    )


async def list_vendors(session: AsyncSession, include_archived: bool = False) -> list[VendorOut]:
    stmt = select(Vendor).order_by(Vendor.name)
    if not include_archived:
        stmt = stmt.where(Vendor.archived_at.is_(None))
    vendors = list(await session.scalars(stmt))
    products: dict[uuid.UUID, list[VendorProductOut]] = defaultdict(list)
    for product in await session.scalars(
        select(Product).where(Product.archived_at.is_(None)).order_by(Product.name)
    ):
        products[product.vendor_id].append(VendorProductOut(id=product.id, name=product.name))
    counted = await session.execute(
        select(VendorContact.vendor_id, func.count())
        .where(VendorContact.archived_at.is_(None))
        .group_by(VendorContact.vendor_id)
    )
    counts = {vendor_id: count for vendor_id, count in counted.tuples()}
    return [
        VendorOut(
            id=vendor.id,
            name=vendor.name,
            products=products.get(vendor.id, []),
            contacts=counts.get(vendor.id, 0),
            archived_at=vendor.archived_at,
        )
        for vendor in vendors
    ]


async def _vendor(session: AsyncSession, vendor_id: uuid.UUID) -> Vendor:
    vendor = await session.get(Vendor, vendor_id)
    if vendor is None:
        raise AppError(ErrorCode.NOT_FOUND, "Вендор не найден.")
    return vendor


async def list_contacts(
    session: AsyncSession, user: CurrentUser, vendor_id: uuid.UUID, trace_id: str | None = None
) -> list[VendorContactOut]:
    """Просмотр контактов — обращение к персональным данным, поэтому пишется в аудит."""
    await _vendor(session, vendor_id)
    contacts = list(
        await session.scalars(
            select(VendorContact)
            .where(VendorContact.vendor_id == vendor_id, VendorContact.archived_at.is_(None))
            .order_by(VendorContact.full_name)
        )
    )
    products = await _products_of(session, [contact.id for contact in contacts])
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="vendor_contact.viewed",
            entity_kind="vendor",
            entity_id=vendor_id,
            after={"contacts": len(contacts)},
            trace_id=trace_id,
        )
    )
    await session.commit()
    return [_contact_out(contact, products.get(contact.id)) for contact in contacts]


async def _link_products(
    session: AsyncSession, contact: VendorContact, product_ids: list[uuid.UUID]
) -> None:
    await session.execute(
        delete(vendor_contact_product).where(vendor_contact_product.c.contact_id == contact.id)
    )
    if product_ids:
        await session.execute(
            vendor_contact_product.insert(),
            [{"contact_id": contact.id, "product_id": product_id} for product_id in product_ids],
        )


async def create_contact(
    session: AsyncSession,
    user: CurrentUser,
    vendor_id: uuid.UUID,
    payload: VendorContactCreate,
    trace_id: str | None = None,
) -> VendorContactOut:
    await _vendor(session, vendor_id)
    _require_key(payload.email, payload.phone)
    products = list(
        await session.scalars(select(Product).where(Product.id.in_(payload.product_ids)))
    )
    if len(products) != len(set(payload.product_ids)) or any(
        product.vendor_id != vendor_id for product in products
    ):
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Контакт отвечает только за продукты своего вендора.",
            errors=[FieldError(field="product_ids", message="Продукт другого вендора")],
        )
    taken = await session.scalar(
        select(VendorContact.id).where(
            VendorContact.vendor_id == vendor_id,
            VendorContact.name_key == normalize(payload.full_name),
            VendorContact.archived_at.is_(None),
        )
    )
    if taken is not None:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Такой контакт у вендора уже есть.",
            errors=[FieldError(field="full_name", message="Уже в списке")],
        )
    contact = VendorContact(
        vendor_id=vendor_id,
        full_name=payload.full_name,
        email_enc=crypto.encrypt(payload.email),
        phone_enc=crypto.encrypt(payload.phone),
        channels=list(dict.fromkeys(payload.channels)),
    )
    session.add(contact)
    await session.flush()
    await _link_products(session, contact, [product.id for product in products])
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="vendor_contact.created",
            entity_kind="vendor_contact",
            entity_id=contact.id,
            after={"vendor_id": str(vendor_id), "products": len(products)},
            trace_id=trace_id,
        )
    )
    await session.commit()
    linked = await _products_of(session, [contact.id])
    return _contact_out(contact, linked.get(contact.id))


async def archive_contact(
    session: AsyncSession, user: CurrentUser, contact_id: uuid.UUID, trace_id: str | None = None
) -> VendorContactOut:
    contact = await session.get(VendorContact, contact_id)
    if contact is None or contact.archived_at is not None:
        raise AppError(ErrorCode.NOT_FOUND, "Контакт не найден.")
    contact.archived_at = datetime.now(UTC)
    # Контакт больше не нужен для работы: хранить его почту и телефон незачем.
    contact.email_enc = None
    contact.phone_enc = None
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="vendor_contact.archived",
            entity_kind="vendor_contact",
            entity_id=contact.id,
            trace_id=trace_id,
        )
    )
    await session.commit()
    return _contact_out(contact)


async def upsert_contact(
    session: AsyncSession,
    vendor: Vendor,
    products: list[Product],
    full_name: str,
    email: str | None,
    phone: str | None,
    channels: list[str],
) -> list[str]:
    """Строка таблицы вендоров: находит человека по ФИО у вендора или заводит его.

    Возвращает, что поменялось; пустой список — строка ничего не изменила. Пустая ячейка
    не стирает уже известную почту или телефон, как и в остальных справочниках.
    """
    _require_key(email, phone)
    contact = await session.scalar(
        select(VendorContact).where(
            VendorContact.vendor_id == vendor.id,
            VendorContact.name_key == normalize(full_name),
            VendorContact.archived_at.is_(None),
        )
    )
    changed: list[str] = []
    if contact is None:
        contact = VendorContact(
            vendor_id=vendor.id,
            full_name=full_name[:200],
            email_enc=crypto.encrypt(email),
            phone_enc=crypto.encrypt(phone),
            channels=channels,
        )
        session.add(contact)
        await session.flush()
        changed.append("контакт")
    else:
        if email and crypto.decrypt(contact.email_enc) != email:
            contact.email_enc = crypto.encrypt(email)
            changed.append("почта")
        if phone and crypto.decrypt(contact.phone_enc) != phone:
            contact.phone_enc = crypto.encrypt(phone)
            changed.append("телефон")
        if channels and list(contact.channels) != channels:
            contact.channels = channels
            changed.append("способ связи")
    known = set(
        await session.scalars(
            select(vendor_contact_product.c.product_id).where(
                vendor_contact_product.c.contact_id == contact.id
            )
        )
    )
    fresh = [product.id for product in products if product.id not in known]
    if fresh:
        await session.execute(
            vendor_contact_product.insert(),
            [{"contact_id": contact.id, "product_id": product_id} for product_id in fresh],
        )
        if "контакт" not in changed:
            changed.append("продукты")
    return changed


async def export_rows(session: AsyncSession) -> list[dict[str, str]]:
    """Строки для выгрузки в формате таблицы кейсодержателя: вендор, продукты, человек."""
    contacts = list(
        await session.execute(
            select(VendorContact, Vendor)
            .join(Vendor, Vendor.id == VendorContact.vendor_id)
            .where(VendorContact.archived_at.is_(None))
            .order_by(Vendor.name, VendorContact.full_name)
        )
    )
    products = await _products_of(session, [contact.id for contact, _ in contacts])
    words = {"email": "Почта", "telegram": "Чат в ТГ", "phone": "Телефон"}
    return [
        {
            "vendor": vendor.name,
            "products": ", ".join(f"«{item.name}»" for item in products.get(contact.id, [])),
            "full_name": contact.full_name,
            "phone": crypto.decrypt(contact.phone_enc) or "",
            "email": crypto.decrypt(contact.email_enc) or "",
            "channels": ", ".join(
                words[channel] for channel in contact.channels if channel in words
            ),
        }
        for contact, vendor in contacts
    ]
