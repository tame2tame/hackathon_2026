import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from app.core.db import SessionDep
from app.core.errors import ErrorCode, TraceIdDep, error_responses
from app.core.pagination import Page, PageQuery
from app.core.roles import Role
from app.core.security import CurrentUser, CurrentUserDep, require_roles
from app.modules.notifications import service
from app.modules.notifications.escalation import escalate_stalled
from app.modules.notifications.schemas import (
    AddressOut,
    AddressUpdate,
    ChannelKind,
    ChannelOut,
    ChannelUpdate,
    DeliveryOut,
    EscalationRunOut,
    NotificationOut,
    ReadAllOut,
)

router = APIRouter(prefix="/api/v1", tags=["notifications"])
admin_router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
AdminDep = Annotated[CurrentUser, Depends(require_roles(Role.ADMIN))]
ADMIN_ERRORS = (
    ErrorCode.AUTH_REQUIRED,
    ErrorCode.AUTH_FORBIDDEN,
    ErrorCode.NOT_FOUND,
    ErrorCode.VALIDATION_ERROR,
)


@router.get(
    "/notifications",
    summary="Мои уведомления",
    description="Сначала новые. Непрочитанные — `unread=true`; их число — поле `total`.",
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.VALIDATION_ERROR),
)
async def read_notifications(
    session: SessionDep,
    user: CurrentUserDep,
    page: PageQuery,
    unread: Annotated[bool, Query(description="Только непрочитанные")] = False,
) -> Page[NotificationOut]:
    return await service.list_notifications(session, user, unread, page)


@router.post(
    "/notifications/read-all",
    summary="Отметить все уведомления прочитанными",
    responses=error_responses(ErrorCode.AUTH_REQUIRED),
)
async def post_read_all(session: SessionDep, user: CurrentUserDep) -> ReadAllOut:
    return ReadAllOut(updated=await service.mark_all_read(session, user))


@router.post(
    "/notifications/{notification_id}/read",
    summary="Отметить уведомление прочитанным",
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND),
)
async def post_read(
    notification_id: uuid.UUID, session: SessionDep, user: CurrentUserDep
) -> NotificationOut:
    return await service.mark_read(session, user, notification_id)


@router.get(
    "/me/notification-addresses",
    summary="Мои адреса в каналах уведомлений",
    description="Куда приходят уведомления: чат Telegram, пользователь Max, почта.",
    responses=error_responses(ErrorCode.AUTH_REQUIRED),
)
async def read_addresses(session: SessionDep, user: CurrentUserDep) -> list[AddressOut]:
    return await service.my_addresses(session, user)


@router.put(
    "/me/notification-addresses/{channel_kind}",
    summary="Задать свой адрес в канале",
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND, ErrorCode.VALIDATION_ERROR
    ),
)
async def put_address(
    channel_kind: ChannelKind, payload: AddressUpdate, session: SessionDep, user: CurrentUserDep
) -> AddressOut:
    return await service.set_address(session, user, channel_kind, payload)


@admin_router.get(
    "/notification-channels",
    summary="Каналы уведомлений",
    description="Telegram, Max и почта. Секреты не показываются: только имя переменной и признак.",
    responses=error_responses(*ADMIN_ERRORS),
)
async def read_channels(session: SessionDep, _admin: AdminDep) -> list[ChannelOut]:
    return await service.list_channels(session)


@admin_router.patch(
    "/notification-channels/{channel_kind}",
    summary="Настроить канал уведомлений",
    description=(
        "Включение, адрес API или почтового сервера, виды уведомлений. Токен или пароль задаётся "
        "переменной окружения `NOTIFY_*`, в базе хранится только её имя."
    ),
    responses=error_responses(*ADMIN_ERRORS),
)
async def patch_channel(
    channel_kind: ChannelKind,
    payload: ChannelUpdate,
    trace_id: TraceIdDep,
    session: SessionDep,
    admin: AdminDep,
) -> ChannelOut:
    return await service.update_channel(session, admin, channel_kind, payload, trace_id)


@admin_router.post(
    "/notification-channels/{channel_kind}/test",
    summary="Пробное сообщение в канал",
    description="Сообщение уходит самому администратору сразу, без очереди; ответ — итог доставки.",
    responses=error_responses(*ADMIN_ERRORS),
)
async def post_channel_test(
    channel_kind: ChannelKind, session: SessionDep, admin: AdminDep
) -> DeliveryOut:
    return await service.send_test(session, admin, channel_kind)


@admin_router.get(
    "/notification-deliveries",
    summary="Журнал доставки уведомлений",
    responses=error_responses(*ADMIN_ERRORS),
)
async def read_deliveries(
    session: SessionDep,
    _admin: AdminDep,
    status: Annotated[
        Literal["pending", "sent", "failed"] | None, Query(description="Состояние доставки")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[DeliveryOut]:
    return await service.list_deliveries(session, status, limit)


@admin_router.post(
    "/escalations/run",
    summary="Проверить зависшие записи сейчас",
    description=(
        "То же, что ночная проверка: записи без изменений дольше срока из настройки "
        "`stalled_escalation` уведомляют руководителя команды или администраторов. "
        "Повторный запуск не дублирует уведомления."
    ),
    responses=error_responses(*ADMIN_ERRORS),
)
async def post_escalations_run(session: SessionDep, _admin: AdminDep) -> EscalationRunOut:
    return EscalationRunOut(notified=await escalate_stalled(session))
