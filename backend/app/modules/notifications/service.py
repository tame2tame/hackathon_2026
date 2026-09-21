"""Уведомления: создание с доставкой в каналы, лента сотрудника, каналы и очередь отправки.

Уведомление всегда появляется в интерфейсе. В Telegram, Max или почту оно уходит, только если
администратор включил канал, канал пересылает этот вид уведомлений, а сотрудник указал свой адрес.
Отправка идёт из очереди воркера и повторяется с нарастающей паузой, поэтому медленный мессенджер
не задерживает переход по этапу.
"""

import logging
import re
import time
import uuid
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import func, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import AppError, ErrorCode, FieldError
from app.core.events import NOTIFICATION_CREATED, get_event_bus
from app.core.pagination import Page, PageParams
from app.core.security import CurrentUser
from app.modules.audit.models import AuditLog
from app.modules.catalogs.models import AppUser, Program, University
from app.modules.clients.models import Client
from app.modules.interactions.models import Interaction
from app.modules.notifications import channels
from app.modules.notifications.models import (
    CHANNEL_KINDS,
    NOTIFICATION_KINDS,
    Notification,
    NotificationAddress,
    NotificationChannel,
    NotificationDelivery,
)
from app.modules.notifications.schemas import (
    AddressOut,
    AddressUpdate,
    ChannelOut,
    ChannelUpdate,
    DeliveryOut,
    NotificationOut,
)

logger = logging.getLogger("radar.notifications")

MAX_ATTEMPTS = 5
BACKOFF_MINUTES = (1, 5, 15, 60)
DELIVERY_BATCH = 100
# Аренда захвата и предел времени на один запуск: очередь не должна упереться в таймаут задачи.
DELIVERY_LEASE = timedelta(minutes=5)
DELIVERY_BUDGET_SECONDS = 120.0
# Во внешние каналы уходит только заголовок и ссылка: подробности — за входом в систему.
EXTERNAL_BODY = "Подробности — в «Радаре вузов»."
NOTIFICATION_NOT_FOUND = "Уведомление не найдено."

ADDRESS_PATTERNS = {
    # Чат Telegram — число, у групп отрицательное; пользователь Max — число; почта — адрес.
    "telegram": re.compile(r"^-?\d{1,20}$"),
    "max": re.compile(r"^\d{1,20}$"),
    "email": re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
}
ADDRESS_HINTS = {
    "telegram": "Идентификатор чата Telegram — число",
    "max": "Идентификатор пользователя Max — число",
    "email": "Адрес почты вида name@example.com",
}


class MessengerSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_url: str = Field(pattern=r"^https?://[^\s]+$", max_length=300)


class EmailSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: str = Field(min_length=1, max_length=253)
    port: int = Field(ge=1, le=65535)
    sender: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=254)
    username: str | None = Field(default=None, max_length=254)
    starttls: bool = False


def _default_channels(settings: Settings) -> dict[str, tuple[str, dict[str, Any], str]]:
    return {
        "telegram": ("Telegram", {"base_url": settings.telegram_api_url}, "NOTIFY_TELEGRAM_TOKEN"),
        "max": ("Max", {"base_url": settings.max_api_url}, "NOTIFY_MAX_TOKEN"),
        "email": (
            "Почта",
            {
                "host": settings.smtp_host,
                "port": settings.smtp_port,
                "sender": settings.smtp_sender,
                "starttls": False,
            },
            "NOTIFY_SMTP_PASSWORD",
        ),
    }


async def ensure_channels(session: AsyncSession) -> dict[str, NotificationChannel]:
    """Три канала, выключенные до решения администратора. Идемпотентна."""
    existing = {
        channel.kind: channel for channel in await session.scalars(select(NotificationChannel))
    }
    for kind, (name, defaults, secret_ref) in _default_channels(get_settings()).items():
        if kind in existing:
            continue
        channel = NotificationChannel(
            kind=kind,
            name=name,
            is_enabled=False,
            is_mock=True,
            settings=defaults,
            secret_ref=secret_ref,
            kinds=[kind for kind in NOTIFICATION_KINDS if kind != "channel_test"],
        )
        session.add(channel)
        existing[kind] = channel
    await session.flush()
    return existing


async def notify(
    session: AsyncSession,
    recipients: Sequence[uuid.UUID],
    kind: str,
    title: str,
    body: str,
    *,
    interaction_id: uuid.UUID | None = None,
    payload: dict[str, Any] | None = None,
    dedupe_key: str | None = None,
) -> list[uuid.UUID]:
    """Уведомляет каждого получателя и ставит доставку в его каналы. Возвращает новые id.

    С `dedupe_key` повторное уведомление того же получателя о том же событии пропускается.
    """
    users = list(dict.fromkeys(recipients))
    if not users:
        return []
    rows = [
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "kind": kind,
            "title": title[:200],
            "body": body,
            "interaction_id": interaction_id,
            "payload": payload or {},
            "dedupe_key": f"{dedupe_key}:{user_id}" if dedupe_key else None,
        }
        for user_id in users
    ]
    created = (
        (
            await session.execute(
                insert(Notification)
                .values(rows)
                .on_conflict_do_nothing(index_elements=[Notification.dedupe_key])
                .returning(Notification.id, Notification.user_id)
            )
        )
        .tuples()
        .all()
    )
    if not created:
        return []

    enabled = {
        channel.kind: channel
        for channel in await session.scalars(
            select(NotificationChannel).where(NotificationChannel.is_enabled.is_(True))
        )
    }
    addresses: dict[uuid.UUID, list[str]] = defaultdict(list)
    if enabled:
        for address in await session.scalars(
            select(NotificationAddress).where(
                NotificationAddress.user_id.in_([user_id for _, user_id in created]),
                NotificationAddress.is_enabled.is_(True),
                NotificationAddress.channel_kind.in_(list(enabled)),
            )
        ):
            if kind in enabled[address.channel_kind].kinds:
                addresses[address.user_id].append(address.channel_kind)
    for notification_id, user_id in created:
        for channel_kind in addresses[user_id]:
            session.add(
                NotificationDelivery(notification_id=notification_id, channel_kind=channel_kind)
            )
    await session.flush()

    bus = get_event_bus()
    for notification_id, user_id in created:
        await bus.publish(
            NOTIFICATION_CREATED,
            {
                "notification_id": str(notification_id),
                "kind": kind,
                "title": title,
                "interaction_id": str(interaction_id) if interaction_id else None,
            },
            owner_user_id=user_id,
        )
    return [notification_id for notification_id, _ in created]


async def interaction_labels(
    session: AsyncSession, interaction_ids: Sequence[uuid.UUID]
) -> dict[uuid.UUID, str]:
    """«Контрагент — программа» для каждой записи одним запросом."""
    ids = list(dict.fromkeys(interaction_ids))
    if not ids:
        return {}
    rows = (
        await session.execute(
            select(Interaction.id, func.coalesce(University.short_name, Client.name), Program.name)
            .select_from(Interaction)
            .outerjoin(University, University.id == Interaction.university_id)
            .outerjoin(Client, Client.id == Interaction.client_id)
            .join(Program, Program.id == Interaction.program_id)
            .where(Interaction.id.in_(ids))
        )
    ).all()
    return {row[0]: f"{row[1]} — {row[2]}" for row in rows}


async def interaction_label(session: AsyncSession, interaction_id: uuid.UUID) -> str:
    """«Контрагент — программа» одной строкой для текста уведомления."""
    labels = await interaction_labels(session, [interaction_id])
    return labels.get(interaction_id, "Взаимодействие")


async def list_notifications(
    session: AsyncSession, user: CurrentUser, unread_only: bool, page: PageParams
) -> Page[NotificationOut]:
    stmt = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    total = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = await session.scalars(
        stmt.order_by(Notification.created_at.desc(), Notification.id)
        .offset(page.offset)
        .limit(page.page_size)
    )
    return Page(
        items=[NotificationOut.model_validate(item) for item in items],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


async def mark_read(
    session: AsyncSession, user: CurrentUser, notification_id: uuid.UUID
) -> NotificationOut:
    notification = await session.scalar(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user.id
        )
    )
    # Чужое уведомление выглядит так же, как несуществующее.
    if notification is None:
        raise AppError(ErrorCode.NOT_FOUND, NOTIFICATION_NOT_FOUND)
    if notification.read_at is None:
        notification.read_at = datetime.now(UTC)
        await session.commit()
    return NotificationOut.model_validate(notification)


async def mark_all_read(session: AsyncSession, user: CurrentUser) -> int:
    result = await session.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.read_at.is_(None))
        .values(read_at=datetime.now(UTC))
    )
    await session.commit()
    return int(getattr(result, "rowcount", 0) or 0)


async def my_addresses(session: AsyncSession, user: CurrentUser) -> list[AddressOut]:
    known = await ensure_channels(session)
    await session.commit()
    mine = {
        address.channel_kind: address
        for address in await session.scalars(
            select(NotificationAddress).where(NotificationAddress.user_id == user.id)
        )
    }
    return [
        AddressOut(
            channel_kind=kind,
            channel_name=known[kind].name,
            channel_enabled=known[kind].is_enabled,
            address=mine[kind].address if kind in mine else None,
            is_enabled=mine[kind].is_enabled if kind in mine else False,
        )
        for kind in CHANNEL_KINDS
    ]


async def set_address(
    session: AsyncSession, user: CurrentUser, channel_kind: str, payload: AddressUpdate
) -> AddressOut:
    pattern = ADDRESS_PATTERNS.get(channel_kind)
    if pattern is None:
        raise AppError(ErrorCode.NOT_FOUND, "Такого канала нет.")
    value = payload.address.strip()
    if not pattern.match(value):
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Адрес не подходит для этого канала.",
            errors=[FieldError(field="address", message=ADDRESS_HINTS[channel_kind])],
        )
    address = await session.get(NotificationAddress, (user.id, channel_kind))
    if address is None:
        address = NotificationAddress(user_id=user.id, channel_kind=channel_kind, address=value)
        session.add(address)
    address.address = value
    address.is_enabled = payload.is_enabled
    await session.commit()
    return next(
        item for item in await my_addresses(session, user) if item.channel_kind == channel_kind
    )


def _channel_out(channel: NotificationChannel) -> ChannelOut:
    return ChannelOut(
        kind=channel.kind,
        name=channel.name,
        is_enabled=channel.is_enabled,
        is_mock=channel.is_mock,
        settings=channel.settings,
        secret_ref=channel.secret_ref,
        secret_configured=channels.secret(channel) is not None,
        kinds=list(channel.kinds),
        updated_at=channel.updated_at,
    )


async def list_channels(session: AsyncSession) -> list[ChannelOut]:
    known = await ensure_channels(session)
    await session.commit()
    return [_channel_out(known[kind]) for kind in CHANNEL_KINDS]


async def _channel(session: AsyncSession, kind: str) -> NotificationChannel:
    channel = (await ensure_channels(session)).get(kind)
    if channel is None:
        raise AppError(ErrorCode.NOT_FOUND, "Такого канала нет.")
    return channel


async def update_channel(
    session: AsyncSession,
    admin: CurrentUser,
    kind: str,
    payload: ChannelUpdate,
    trace_id: str | None = None,
) -> ChannelOut:
    channel = await _channel(session, kind)
    before = {"is_enabled": channel.is_enabled, "settings": channel.settings}
    previous_host = channels.host_of(channel)
    if payload.settings is not None:
        schema: type[BaseModel] = EmailSettings if kind == "email" else MessengerSettings
        try:
            channel.settings = schema.model_validate(payload.settings).model_dump(mode="json")
        except ValidationError as error:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Настройки канала не прошли проверку.",
                errors=[
                    FieldError(
                        field=".".join(["settings", *(str(part) for part in item["loc"])]),
                        message=item["msg"],
                    )
                    for item in error.errors()
                ],
            ) from error
        if not channels.host_allowed(channels.host_of(channel)):
            allowed = ", ".join(get_settings().notify_allowed_host_list)
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                f"Адрес канала не разрешён. Разрешены: {allowed}.",
                errors=[
                    FieldError(
                        field="settings.host" if kind == "email" else "settings.base_url",
                        message="Адрес не входит в NOTIFY_ALLOWED_HOSTS",
                    )
                ],
            )
    if payload.is_enabled is not None:
        channel.is_enabled = payload.is_enabled
    if payload.is_mock is not None:
        channel.is_mock = payload.is_mock
    if "secret_ref" in payload.model_fields_set:
        channel.secret_ref = payload.secret_ref
    elif channels.host_of(channel) != previous_host:
        # Адрес сменился — прежний секрет к нему не привязан: его называют заново.
        channel.secret_ref = None
    if payload.kinds is not None:
        channel.kinds = list(dict.fromkeys(payload.kinds))
    channel.updated_by = admin.id
    # Секрет в журнал не попадает: он и в базе не хранится, только имя переменной.
    session.add(
        AuditLog(
            actor_user_id=admin.id,
            action="admin.notification_channel_changed",
            entity_kind="notification_channel",
            before=before,
            after={"kind": kind, "is_enabled": channel.is_enabled, "settings": channel.settings},
            trace_id=trace_id,
        )
    )
    await session.commit()
    await session.refresh(channel)
    return _channel_out(channel)


def _link(notification: Notification) -> str | None:
    if notification.interaction_id is None:
        return None
    return f"{get_settings().public_url.rstrip('/')}/interactions/{notification.interaction_id}"


async def _send(
    delivery: NotificationDelivery,
    notification: Notification,
    channel: NotificationChannel,
    address: str,
    now: datetime,
) -> None:
    delivery.attempts += 1
    # Персональные данные во внешний канал не уходят: только заголовок события и ссылка.
    body = notification.body if notification.kind == "channel_test" else EXTERNAL_BODY
    failure: str | None = None
    try:
        await channels.sender_for(channel).send(
            channels.OutgoingMessage(address, notification.title, body, _link(notification))
        )
    except channels.DeliveryError as error:
        failure = str(error)
    except Exception as error:
        # Сбой отправителя не должен останавливать очередь: он становится обычным отказом доставки.
        logger.exception("Канал %s не отправил уведомление %s", channel.kind, notification.id)
        failure = type(error).__name__
    if failure is None:
        delivery.status = "sent"
        delivery.sent_at = now
        delivery.last_error = None
        return
    delivery.last_error = failure[:300]
    if delivery.attempts >= MAX_ATTEMPTS:
        delivery.status = "failed"
    else:
        pause = BACKOFF_MINUTES[min(delivery.attempts, len(BACKOFF_MINUTES)) - 1]
        delivery.next_attempt_at = now + timedelta(minutes=pause)


async def send_test(session: AsyncSession, admin: CurrentUser, kind: str) -> DeliveryOut:
    """Пробное сообщение администратору: канал проверяется до того, как его включат для всех."""
    channel = await _channel(session, kind)
    address = await session.get(NotificationAddress, (admin.id, kind))
    if address is None:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Сначала укажите свой адрес в этом канале: пробное сообщение придёт вам.",
            errors=[FieldError(field="address", message="Адрес не задан")],
        )
    now = datetime.now(UTC)
    notification = Notification(
        user_id=admin.id,
        kind="channel_test",
        title=f"Проверка канала «{channel.name}»",
        body="Если вы видите это сообщение, канал уведомлений «Радара вузов» работает.",
        payload={},
    )
    session.add(notification)
    await session.flush()
    delivery = NotificationDelivery(notification_id=notification.id, channel_kind=kind)
    session.add(delivery)
    await session.flush()
    await _send(delivery, notification, channel, address.address, now)
    if delivery.status == "pending":
        # Пробное сообщение не повторяется: администратор видит результат сразу.
        delivery.status = "failed"
    await session.commit()
    return DeliveryOut.model_validate(delivery)


async def list_deliveries(
    session: AsyncSession, status: str | None, limit: int = 100
) -> list[DeliveryOut]:
    stmt = (
        select(NotificationDelivery).order_by(NotificationDelivery.created_at.desc()).limit(limit)
    )
    if status:
        stmt = stmt.where(NotificationDelivery.status == status)
    return [DeliveryOut.model_validate(item) for item in await session.scalars(stmt)]


@dataclass(slots=True)
class DeliveryStats:
    sent: int = 0
    retried: int = 0
    failed: int = 0


async def deliver_pending(session: AsyncSession, now: datetime | None = None) -> DeliveryStats:
    """Отправляет созревшие доставки.

    Захват фиксируется до сети, каждая доставка сохраняется отдельно, а остаток очереди
    возвращается назад по истечении времени запуска: медленный канал не блокирует остальные
    и не откатывает уже отправленное.
    """
    now = now or datetime.now(UTC)
    due = (
        select(NotificationDelivery.id)
        .where(
            NotificationDelivery.status == "pending",
            NotificationDelivery.next_attempt_at <= now,
            or_(
                NotificationDelivery.locked_until.is_(None),
                NotificationDelivery.locked_until < now,
            ),
        )
        .order_by(NotificationDelivery.next_attempt_at)
        .limit(DELIVERY_BATCH)
        .with_for_update(skip_locked=True)
    )
    claimed = list(
        await session.scalars(
            update(NotificationDelivery)
            .where(NotificationDelivery.id.in_(due.scalar_subquery()))
            .values(locked_until=now + DELIVERY_LEASE)
            .returning(NotificationDelivery.id)
        )
    )
    await session.commit()

    stats = DeliveryStats()
    started = time.monotonic()
    for index, delivery_id in enumerate(claimed):
        if time.monotonic() - started > DELIVERY_BUDGET_SECONDS:
            await session.execute(
                update(NotificationDelivery)
                .where(NotificationDelivery.id.in_(claimed[index:]))
                .values(locked_until=None)
            )
            await session.commit()
            break
        await _deliver_one(session, delivery_id, now, stats)
    return stats


async def _deliver_one(
    session: AsyncSession, delivery_id: uuid.UUID, now: datetime, stats: DeliveryStats
) -> None:
    row = (
        (
            await session.execute(
                select(NotificationDelivery, Notification, NotificationChannel, AppUser)
                .join(Notification, Notification.id == NotificationDelivery.notification_id)
                .join(
                    NotificationChannel,
                    NotificationChannel.kind == NotificationDelivery.channel_kind,
                )
                .join(AppUser, AppUser.id == Notification.user_id)
                .where(NotificationDelivery.id == delivery_id)
            )
        )
        .tuples()
        .one_or_none()
    )
    if row is None:
        return
    delivery, notification, channel, user = row
    address = await session.get(NotificationAddress, (user.id, channel.kind))
    if not channel.is_enabled or address is None or not address.is_enabled or not user.is_active:
        delivery.status = "failed"
        delivery.last_error = "Канал выключен или сотрудник отписался"
        stats.failed += 1
    else:
        await _send(delivery, notification, channel, address.address, now)
        match delivery.status:
            case "sent":
                stats.sent += 1
            case "failed":
                stats.failed += 1
            case _:
                stats.retried += 1
    delivery.locked_until = None
    # Каждая доставка фиксируется сама: ошибка одной не отменяет уже отправленные.
    await session.commit()
