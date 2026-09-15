"""Каталоги и профиль: вузы и счётчики в области видимости, справочники, пользователи."""

import uuid
from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.errors import AppError, ErrorCode
from app.core.pagination import Page, PageParams
from app.core.roles import Role
from app.core.scope import apply_interaction_scope, scope_name
from app.core.security import CurrentUser
from app.modules.catalogs.models import AppUser, Direction, Product, Program, University
from app.modules.catalogs.schemas import (
    DirectionRef,
    MeOut,
    ProductRef,
    ProgramRef,
    TeamRef,
    UniversityOut,
    UserOut,
)
from app.modules.interactions.models import Interaction
from app.modules.radar.models import RadarSignal
from app.modules.radar.service import like_pattern


async def get_me(session: AsyncSession, user: CurrentUser) -> MeOut:
    db_user = await session.scalar(
        select(AppUser).where(AppUser.id == user.id).options(joinedload(AppUser.team))
    )
    if db_user is None:
        raise AppError(ErrorCode.AUTH_REQUIRED, "Пользователь не найден.")
    return MeOut(
        id=db_user.id,
        email=db_user.email,
        full_name=db_user.full_name,
        role=user.role,
        team=TeamRef.model_validate(db_user.team) if db_user.team else None,
        scope=scope_name(user),
    )


def _universities_query(user: CurrentUser) -> Select[Any]:
    scoped = apply_interaction_scope(
        select(Interaction.id, Interaction.university_id).where(Interaction.status != "cancelled"),
        user,
    ).subquery()
    interactions = (
        select(scoped.c.university_id, func.count().label("total"))
        .group_by(scoped.c.university_id)
        .subquery()
    )
    signals = (
        select(scoped.c.university_id, func.count(RadarSignal.id).label("total"))
        .join(RadarSignal, RadarSignal.interaction_id == scoped.c.id)
        .where(RadarSignal.resolved_at.is_(None))
        .group_by(scoped.c.university_id)
        .subquery()
    )
    stmt = (
        select(
            University,
            func.coalesce(interactions.c.total, 0),
            func.coalesce(signals.c.total, 0),
        )
        .outerjoin(interactions, interactions.c.university_id == University.id)
        .outerjoin(signals, signals.c.university_id == University.id)
        .where(University.archived_at.is_(None))
    )
    # Администратор видит весь каталог, остальные — только вузы со своими взаимодействиями.
    if user.role is not Role.ADMIN:
        stmt = stmt.where(interactions.c.total > 0)
    return stmt


def _university_out(university: University, interactions: int, signals: int) -> UniversityOut:
    return UniversityOut(
        id=university.id,
        name=university.name,
        short_name=university.short_name,
        region=university.region,
        city=university.city,
        interactions_count=interactions,
        open_signals_count=signals,
    )


async def list_universities(
    session: AsyncSession, user: CurrentUser, search: str | None, page: PageParams
) -> Page[UniversityOut]:
    stmt = _universities_query(user)
    if search:
        pattern = like_pattern(search)
        stmt = stmt.where(
            or_(
                University.name.ilike(pattern, escape="\\"),
                University.short_name.ilike(pattern, escape="\\"),
                University.region.ilike(pattern, escape="\\"),
            )
        )
    total = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = await session.execute(
        stmt.order_by(University.name).offset(page.offset).limit(page.page_size)
    )
    return Page(
        items=[_university_out(u, i, s) for u, i, s in rows.tuples()],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


async def get_university(
    session: AsyncSession, user: CurrentUser, university_id: uuid.UUID
) -> UniversityOut:
    row = (
        await session.execute(_universities_query(user).where(University.id == university_id))
    ).first()
    if row is None:
        raise AppError(ErrorCode.NOT_FOUND, "Вуз не найден или недоступен.")
    university, interactions, signals = row.tuple()
    return _university_out(university, interactions, signals)


async def list_directions(session: AsyncSession) -> list[DirectionRef]:
    directions = await session.scalars(select(Direction).order_by(Direction.name))
    return [DirectionRef.model_validate(d) for d in directions]


async def list_programs(
    session: AsyncSession, direction_id: list[uuid.UUID] | None
) -> list[ProgramRef]:
    stmt = select(Program).options(joinedload(Program.direction)).order_by(Program.name)
    if direction_id:
        stmt = stmt.where(Program.direction_id.in_(direction_id))
    return [ProgramRef.model_validate(p) for p in await session.scalars(stmt)]


async def list_products(session: AsyncSession) -> list[ProductRef]:
    products = await session.scalars(
        select(Product).options(joinedload(Product.vendor)).order_by(Product.name)
    )
    return [ProductRef.model_validate(p) for p in products]


async def list_users(session: AsyncSession, user: CurrentUser) -> list[UserOut]:
    """Пользователи для фильтров «ответственный»: КАМ видит себя, руководитель — команду."""
    stmt = select(AppUser).where(AppUser.is_active.is_(True)).order_by(AppUser.full_name)
    match scope_name(user):
        case "own":
            stmt = stmt.where(AppUser.id == user.id)
        case "team":
            stmt = stmt.where(or_(AppUser.team_id == user.team_id, AppUser.id == user.id))
        case "all":
            pass
    return [UserOut.model_validate(u) for u in await session.scalars(stmt)]
