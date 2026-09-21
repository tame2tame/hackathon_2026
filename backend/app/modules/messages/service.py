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
from app.modules.notifications.service import interaction_labels

PREVIEW = 120
DIALOG_LIMIT = 200


async def _peer(
    session: AsyncSession, user: CurrentUser, peer_id: uuid.UUID, *, active_only: bool = True
) -> AppUser:
    """Собеседник. Уволенному писать нельзя, но прочитать переписку с ним — можно."""
    if peer_id == user.id:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Сообщение самому себе — это заметка: она есть в карточке записи.",
            errors=[FieldError(field="recipient_id", message="Нужен другой сотрудник")],
        )
    stmt = select(AppUser).where(AppUser.id == peer_id)
    if active_only:
        stmt = stmt.where(AppUser.is_active.is_(True))
    peer = await session.scalar(stmt)
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
    visible = list(
        await session.scalars(
            apply_interaction_scope(select(Interaction.id).where(Interaction.id.in_(wanted)), user)
        )
    )
    return await interaction_labels(session, visible)


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
    await _peer(session, user, peer_id, active_only=False)
    messages = list(
        await session.scalars(
            select(Message)
            .where(
                or_(
                    (Message.sender_id == user.id) & (Message.recipient_id == peer_id),
                    (Message.sender_id == peer_id) & (Message.recipient_id == user.id),
                )
            )
            .order_by(Message.created_at.desc(), Message.id.desc())
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
    """С кем и о чём шла переписка: последнее сообщение и число непрочитанных.

    Собеседник, последнее сообщение и счётчик берутся одним запросом: при полусотне диалогов
    запрос на каждый из них обошёлся бы дороже самого ответа.
    """
    peer = case(
        (Message.sender_id == user.id, Message.recipient_id), else_=Message.sender_id
    ).label("peer_id")
    mine = select(
        peer,
        Message.body,
        Message.created_at,
        ((Message.recipient_id == user.id) & Message.read_at.is_(None)).label("is_unread"),
    ).where(or_(Message.sender_id == user.id, Message.recipient_id == user.id))
    dialog = mine.subquery()
    last = (
        select(dialog.c.peer_id, dialog.c.body, dialog.c.created_at)
        .distinct(dialog.c.peer_id)
        .order_by(dialog.c.peer_id, dialog.c.created_at.desc())
        .subquery()
    )
    counts = (
        select(
            dialog.c.peer_id,
            func.count().filter(dialog.c.is_unread).label("unread"),
        )
        .group_by(dialog.c.peer_id)
        .subquery()
    )
    rows = (
        await session.execute(
            select(AppUser, last.c.body, last.c.created_at, counts.c.unread)
            .join(last, last.c.peer_id == AppUser.id)
            .join(counts, counts.c.peer_id == AppUser.id)
            .order_by(last.c.created_at.desc())
        )
    ).all()
    items = [
        DialogOut(
            peer=UserRef.model_validate(person),
            last_message=(body or "")[:PREVIEW],
            last_at=last_at,
            unread=unread,
        )
        for person, body, last_at, unread in rows
    ]
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
    await _peer(session, user, peer_id, active_only=False)
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
