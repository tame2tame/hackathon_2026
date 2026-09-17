import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.db import SessionDep
from app.core.errors import ErrorCode, TraceIdDep, error_responses
from app.core.pagination import Page, PageQuery
from app.core.roles import Role
from app.core.security import CurrentUser, CurrentUserDep, require_roles
from app.modules.catalogs.schemas import (
    CounterpartyGroupOut,
    DirectionRef,
    MeOut,
    PriorityUpdate,
    ProductRef,
    ProgramRef,
    UniversityOut,
    UserOut,
)
from app.modules.catalogs.service import (
    get_me,
    get_university,
    list_directions,
    list_groups,
    list_products,
    list_programs,
    list_universities,
    list_users,
    set_program_priority,
)

router = APIRouter(prefix="/api/v1", tags=["catalogs"])
ManagerDep = Annotated[CurrentUser, Depends(require_roles(Role.MANAGER, Role.ADMIN))]

AUTH_ERRORS = error_responses(ErrorCode.AUTH_REQUIRED)
LIST_ERRORS = error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.VALIDATION_ERROR)


@router.get("/me", summary="Профиль текущего пользователя", responses=AUTH_ERRORS)
async def read_me(session: SessionDep, user: CurrentUserDep) -> MeOut:
    return await get_me(session, user)


@router.get(
    "/universities",
    summary="Вузы со счётчиками взаимодействий и открытых сигналов",
    responses=LIST_ERRORS,
)
async def read_universities(
    session: SessionDep,
    user: CurrentUserDep,
    page: PageQuery,
    search: Annotated[str | None, Query(max_length=100, description="Название или регион")] = None,
) -> Page[UniversityOut]:
    query = search.strip() if search and search.strip() else None
    return await list_universities(session, user, query, page)


@router.get(
    "/universities/{university_id}",
    summary="Вуз",
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND),
)
async def read_university(
    university_id: uuid.UUID, session: SessionDep, user: CurrentUserDep
) -> UniversityOut:
    return await get_university(session, user, university_id)


@router.get(
    "/counterparty-groups",
    summary="Группы контрагентов",
    description="Вузы (B2B), частные лица (B2C) и группы, которые завёл администратор.",
    responses=AUTH_ERRORS,
)
async def read_groups(session: SessionDep, _user: CurrentUserDep) -> list[CounterpartyGroupOut]:
    return await list_groups(session)


@router.get("/directions", summary="ИТ-направления", responses=AUTH_ERRORS)
async def read_directions(session: SessionDep, _user: CurrentUserDep) -> list[DirectionRef]:
    return await list_directions(session)


@router.get("/programs", summary="ИТ-программы", responses=LIST_ERRORS)
async def read_programs(
    session: SessionDep,
    _user: CurrentUserDep,
    direction_id: Annotated[list[uuid.UUID] | None, Query(description="ИТ-направление")] = None,
) -> list[ProgramRef]:
    return await list_programs(session, direction_id)


@router.put(
    "/programs/{program_id}/priority",
    summary="Задать приоритет курса вручную",
    description=(
        "Рейтинг востребованности считается по данным LMS и сайта, но порядок продвижения можно "
        "задать руками: приоритет показывается в справочнике и в рейтинге. Меняют руководитель "
        "и администратор, изменение пишется в аудит."
    ),
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED,
        ErrorCode.AUTH_FORBIDDEN,
        ErrorCode.NOT_FOUND,
        ErrorCode.VALIDATION_ERROR,
    ),
)
async def put_program_priority(
    program_id: uuid.UUID,
    payload: PriorityUpdate,
    trace_id: TraceIdDep,
    session: SessionDep,
    user: ManagerDep,
) -> ProgramRef:
    return await set_program_priority(session, user, program_id, payload.priority, trace_id)


@router.get("/products", summary="ИТ-продукты", responses=AUTH_ERRORS)
async def read_products(session: SessionDep, _user: CurrentUserDep) -> list[ProductRef]:
    return await list_products(session)


@router.get("/users", summary="Пользователи для фильтра «ответственный»", responses=AUTH_ERRORS)
async def read_users(session: SessionDep, user: CurrentUserDep) -> list[UserOut]:
    return await list_users(session, user)
