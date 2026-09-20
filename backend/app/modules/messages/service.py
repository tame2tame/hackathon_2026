"""Переписка внутри сервиса: КАМ и руководитель обсуждают запись, не выходя из системы.

Сообщение видят только двое: отправитель и получатель. Запись, о которой идёт речь, читатель
видит ссылкой, только если она в его области видимости — иначе в сообщении останется текст,
но не появится ссылка на чужую карточку (ADR-007).
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import case, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ErrorCode, FieldError
from app.core.events import MESSAGE_CREATED, get_event_bus
from app.core.scope import apply_interaction_scope
from app.core.security import CurrentUser
from app.modules.catalogs.models import AppUser
from app.modules.catalogs.schemas import UserRef
from app.modules.interactions.models import Interaction
from app.modules.messages.models import Message
from app.modules.messages.schemas import (
    DialogOut,
    DialogsOut,
    MessageCreate,
    MessageInteractionRef,
    MessageOut,
)
from app.modules.notifications.service import interaction_label

PREVIEW = 120
DIALOG_LIMIT = 200


async def _peer(session: AsyncSession, user: CurrentUser, peer_id: uuid.UUID) -> AppUser:
    if peer_id == user.id:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Сообщение самому себе — это заметка: она есть в карточке записи.",
            errors=[FieldError(field="recipient_id", message="Нужен другой сотрудник")],
        )
    peer = await session.scalar(
        select(AppUser).where(AppUser.id == peer_id, AppUser.is_active.is_(True))
    )
    if peer is None:
        raise AppError(ErrorCode.NOT_FOUND, "Сотрудник не найден.")
    return peer


async def _visible_labels(
    session: AsyncSession, user: CurrentUser, messages: list[Message]
) -> dict[uuid.UUID, str]:
    """Подписи записей, доступных читателю: чужие в переписке остаются без ссылки."""
    wanted = {message.interaction_id for message in messages if message.interaction_id}
    if not wanted:
        return {}
    visible = await session.scalars(
        apply_interaction_scope(select(Interaction.id).where(Interaction.id.in_(wanted)), user)
    )
    return {item: await interaction_label(session, item) for item in visible}


def _out(
    message: Message, people: dict[uuid.UUID, AppUser], labels: dict[uuid.UUID, str]
) -> MessageOut:
    reference = None
    if message.interaction_id and message.interaction_id in labels:
        reference = MessageInteractionRef(
            id=message.interaction_id, label=labels[message.interaction_id]
        )
    return MessageOut(
        id=message.id,
        sender=UserRef.model_validate(people[message.sender_id]),
        recipient=UserRef.model_validate(people[message.recipient_id]),
        body=message.body,
        interaction=reference,
        created_at=message.created_at,
        read_at=message.read_at,
    )


async def _people(session: AsyncSession, messages: list[Message]) -> dict[uuid.UUID, AppUser]:
    ids = {message.sender_id for message in messages} | {m.recipient_id for m in messages}
    return {
        person.id: person
        for person in await session.scalars(select(AppUser).where(AppUser.id.in_(ids)))
    }


async def read_dialog(
    session: AsyncSession, user: CurrentUser, peer_id: uuid.UUID, limit: int = 50
) -> list[MessageOut]:
    """Переписка с одним собеседником: сначала старые, чтобы читать сверху вниз."""
    await _peer(session, user, peer_id)
    messages = list(
        await session.scalars(
            select(Message)
            .where(
                or_(
                    (Message.sender_id == user.id) & (Message.recipient_id == peer_id),
                    (Message.sender_id == peer_id) & (Message.recipient_id == user.id),
                )
            )
            .order_by(Message.created_at.desc())
            .limit(min(limit, DIALOG_LIMIT))
        )
    )
    messages.reverse()
    if not messages:
        return []
    people = await _people(session, messages)
    labels = await _visible_labels(session, user, messages)
    return [_out(message, people, labels) for message in messages]


async def list_dialogs(session: AsyncSession, user: CurrentUser) -> DialogsOut:
    """С кем и о чём шла переписка: последнее сообщение и число непрочитанных."""
    peer = case(
        (Message.sender_id == user.id, Message.recipient_id), else_=Message.sender_id
    ).label("peer_id")
    rows = (
        await session.execute(
            select(
                peer,
                func.max(Message.created_at).label("last_at"),
                func.count()
                .filter(Message.recipient_id == user.id, Message.read_at.is_(None))
                .label("unread"),
            )
            .where(or_(Message.sender_id == user.id, Message.recipient_id == user.id))
            .group_by(peer)
            .order_by(func.max(Message.created_at).desc())
        )
    ).all()
    if not rows:
        return DialogsOut(unread_total=0, items=[])

    people = {
        person.id: person
        for person in await session.scalars(
            select(AppUser).where(AppUser.id.in_([row.peer_id for row in rows]))
        )
    }
    items: list[DialogOut] = []
    for row in rows:
        last = await session.scalar(
            select(Message.body)
            .where(
                or_(
                    (Message.sender_id == user.id) & (Message.recipient_id == row.peer_id),
                    (Message.sender_id == row.peer_id) & (Message.recipient_id == user.id),
                )
            )
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        items.append(
            DialogOut(
                peer=UserRef.model_validate(people[row.peer_id]),
                last_message=(last or "")[:PREVIEW],
                last_at=row.last_at,
                unread=row.unread,
            )
        )
    return DialogsOut(unread_total=sum(item.unread for item in items), items=items)


async def send_message(
    session: AsyncSession, user: CurrentUser, payload: MessageCreate
) -> MessageOut:
    peer = await _peer(session, user, payload.recipient_id)
    if payload.interaction_id is not None:
        # Сослаться можно только на свою запись: иначе ссылка сама рассказала бы о чужой.
        own = await session.scalar(
            apply_interaction_scope(
                select(Interaction.id).where(Interaction.id == payload.interaction_id), user
            )
        )
        if own is None:
            raise AppError(ErrorCode.NOT_FOUND, "Взаимодействие не найдено или недоступно.")
    message = Message(
        sender_id=user.id,
        recipient_id=peer.id,
        interaction_id=payload.interaction_id,
        body=payload.body.strip(),
    )
    session.add(message)
    await session.commit()
    await session.refresh(message)
    await get_event_bus().publish(
        MESSAGE_CREATED,
        {"message_id": str(message.id), "sender_id": str(user.id)},
        owner_user_id=peer.id,
    )
    labels = await _visible_labels(session, user, [message])
    return _out(message, await _people(session, [message]), labels)


async def mark_read(session: AsyncSession, user: CurrentUser, peer_id: uuid.UUID) -> int:
    """Прочитанными становятся только входящие: свои сообщения отмечать нечего."""
    await _peer(session, user, peer_id)
    updated = await session.scalars(
        update(Message)
        .where(
            Message.recipient_id == user.id,
            Message.sender_id == peer_id,
            Message.read_at.is_(None),
        )
        .values(read_at=datetime.now(UTC))
        .returning(Message.id)
    )
    count = len(list(updated))
    await session.commit()
    return count
