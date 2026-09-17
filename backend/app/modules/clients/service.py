"""Клиенты: поиск, карточка с персональными данными и создание.

Организации видны всем: это не персональные данные, а дубль компании дороже лишнего показа.
Людей видит тот, кто с ними работает: создатель, владельцы их записей и руководитель команды.
"""

import uuid
from typing import cast

from sqlalchemy import ColumnElement, Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import crypto
from app.core.errors import AppError, ErrorCode, FieldError
from app.core.pagination import Page, PageParams
from app.core.roles import Role
from app.core.scope import apply_interaction_scope
from app.core.security import CurrentUser
from app.modules.audit.models import AuditLog
from app.modules.catalogs.models import AppUser
from app.modules.clients.models import Client
from app.modules.clients.schemas import ClientCreate, ClientKind, ClientListItem, ClientOut
from app.modules.interactions.models import Interaction
from app.modules.radar.service import like_pattern

CLIENT_NOT_FOUND = "Клиент не найден или недоступен."


def _visible(user: CurrentUser) -> ColumnElement[bool] | None:
    if user.role is Role.ADMIN:
        return None
    worked_with = apply_interaction_scope(
        select(Interaction.client_id).where(Interaction.client_id.is_not(None)), user
    )
    created = Client.created_by == user.id
    if user.role is Role.MANAGER and user.team_id is not None:
        created = Client.created_by.in_(select(AppUser.id).where(AppUser.team_id == user.team_id))
    return or_(Client.kind == "organization", Client.id.in_(worked_with), created)


def visible_clients(user: CurrentUser) -> Select[tuple[Client]]:
    stmt = select(Client)
    condition = _visible(user)
    return stmt if condition is None else stmt.where(condition)


async def visible_client(session: AsyncSession, user: CurrentUser, client_id: uuid.UUID) -> Client:
    client = await session.scalar(visible_clients(user).where(Client.id == client_id))
    if client is None:
        raise AppError(ErrorCode.NOT_FOUND, CLIENT_NOT_FOUND)
    return client


async def list_clients(
    session: AsyncSession,
    user: CurrentUser,
    search: str | None,
    kind: str | None,
    page: PageParams,
) -> Page[ClientListItem]:
    stmt = visible_clients(user).where(Client.archived_at.is_(None))
    if kind:
        stmt = stmt.where(Client.kind == kind)
    if search:
        pattern = like_pattern(search)
        stmt = stmt.where(
            or_(Client.name.ilike(pattern, escape="\\"), Client.inn.ilike(pattern, escape="\\"))
        )
    total = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    clients = await session.scalars(
        stmt.order_by(Client.name, Client.id).offset(page.offset).limit(page.page_size)
    )
    return Page(
        items=[ClientListItem.model_validate(client) for client in clients],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


def _client_out(client: Client, with_contacts: bool = True) -> ClientOut:
    return ClientOut(
        id=client.id,
        kind=cast(ClientKind, client.kind),
        name=client.name,
        inn=client.inn,
        city=client.city,
        email=crypto.decrypt(client.email_enc) if with_contacts else None,
        phone=crypto.decrypt(client.phone_enc) if with_contacts else None,
        archived_at=client.archived_at,
    )


async def works_with(session: AsyncSession, user: CurrentUser, client: Client) -> bool:
    """Свой клиент: администратор, создатель, его команда или владелец записи с этим клиентом."""
    if user.role is Role.ADMIN or client.created_by == user.id:
        return True
    worked_with = apply_interaction_scope(
        select(Interaction.id).where(Interaction.client_id == client.id), user
    )
    if await session.scalar(worked_with) is not None:
        return True
    if user.role is Role.MANAGER and user.team_id is not None and client.created_by is not None:
        team = await session.scalar(
            select(AppUser.id).where(
                AppUser.id == client.created_by, AppUser.team_id == user.team_id
            )
        )
        return team is not None
    return False


async def get_client(
    session: AsyncSession, user: CurrentUser, client_id: uuid.UUID, trace_id: str | None = None
) -> ClientOut:
    """Карточка клиента.

    Организации видны всем, чтобы не плодить дубли, но контакты — персональные данные: их
    показывают только тем, кто с клиентом работает, и каждый такой просмотр пишется в аудит.
    """
    client = await visible_client(session, user, client_id)
    with_contacts = await works_with(session, user, client)
    if with_contacts and (client.email_enc is not None or client.phone_enc is not None):
        session.add(
            AuditLog(
                actor_user_id=user.id,
                action="client.viewed",
                entity_kind="client",
                entity_id=client.id,
                after={"kind": client.kind},
                trace_id=trace_id,
            )
        )
        await session.commit()
    return _client_out(client, with_contacts)


async def create_client(
    session: AsyncSession, user: CurrentUser, payload: ClientCreate, trace_id: str | None = None
) -> ClientOut:
    if (payload.email or payload.phone) and not crypto.is_configured():
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Не настроен ключ шифрования: клиента с персональными данными сохранить нельзя.",
            errors=[FieldError(field="email", message="Шифрование не настроено")],
        )
    if payload.inn and await session.scalar(select(Client.id).where(Client.inn == payload.inn)):
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Организация с таким ИНН уже есть: найдите её в списке клиентов.",
            errors=[FieldError(field="inn", message="ИНН уже занят")],
        )
    client = Client(
        kind=payload.kind,
        name=payload.name.strip(),
        inn=payload.inn,
        city=payload.city,
        email_enc=crypto.encrypt(payload.email),
        phone_enc=crypto.encrypt(payload.phone),
        created_by=user.id,
    )
    session.add(client)
    await session.flush()
    # В журнал идёт факт появления клиента, но не его персональные данные.
    session.add(
        AuditLog(
            actor_user_id=user.id,
            action="client.created",
            entity_kind="client",
            entity_id=client.id,
            after={"kind": client.kind, "has_email": payload.email is not None},
            trace_id=trace_id,
        )
    )
    await session.commit()
    return _client_out(client)
