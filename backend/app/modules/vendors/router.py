import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.db import SessionDep
from app.core.errors import ErrorCode, TraceIdDep, error_responses
from app.core.roles import Role
from app.core.security import CurrentUser, CurrentUserDep, require_roles
from app.modules.vendors import service
from app.modules.vendors.schemas import VendorContactCreate, VendorContactOut, VendorOut

router = APIRouter(prefix="/api/v1", tags=["vendors"])
ManagerDep = Annotated[CurrentUser, Depends(require_roles(Role.MANAGER, Role.ADMIN))]


@router.get(
    "/vendors",
    summary="Вендоры с продуктами",
    description="Справочник вендоров с id, продуктами и числом контактов.",
    responses=error_responses(ErrorCode.AUTH_REQUIRED),
)
async def read_vendors(
    session: SessionDep,
    _user: CurrentUserDep,
    include_archived: Annotated[bool, Query(description="Вместе с архивными")] = False,
) -> list[VendorOut]:
    return await service.list_vendors(session, include_archived)


@router.get(
    "/vendors/{vendor_id}/contacts",
    summary="Контакты вендора",
    description=(
        "Кто отвечает за продукты вендора и как с ним связаться. Почта и телефон — "
        "персональные данные: просмотр пишется в журнал аудита."
    ),
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND),
)
async def read_vendor_contacts(
    vendor_id: uuid.UUID, trace_id: TraceIdDep, session: SessionDep, user: CurrentUserDep
) -> list[VendorContactOut]:
    return await service.list_contacts(session, user, vendor_id, trace_id)


@router.post(
    "/vendors/{vendor_id}/contacts",
    status_code=status.HTTP_201_CREATED,
    summary="Добавить контакт вендора",
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED,
        ErrorCode.AUTH_FORBIDDEN,
        ErrorCode.NOT_FOUND,
        ErrorCode.VALIDATION_ERROR,
    ),
)
async def post_vendor_contact(
    vendor_id: uuid.UUID,
    payload: VendorContactCreate,
    trace_id: TraceIdDep,
    session: SessionDep,
    user: ManagerDep,
) -> VendorContactOut:
    return await service.create_contact(session, user, vendor_id, payload, trace_id)


@router.post(
    "/vendor-contacts/{contact_id}/archive",
    summary="Убрать контакт вендора в архив",
    description="Почта и телефон стираются: хранить их больше незачем.",
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED, ErrorCode.AUTH_FORBIDDEN, ErrorCode.NOT_FOUND
    ),
)
async def post_vendor_contact_archive(
    contact_id: uuid.UUID, trace_id: TraceIdDep, session: SessionDep, user: ManagerDep
) -> VendorContactOut:
    return await service.archive_contact(session, user, contact_id, trace_id)
