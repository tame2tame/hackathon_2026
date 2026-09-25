"""Подключение к PostgreSQL: асинхронный движок, сессии и базовый класс моделей."""

import uuid
from collections.abc import AsyncIterator, Callable
from datetime import datetime
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import get_settings

# Стабильные имена ограничений нужны, чтобы миграции Alembic были воспроизводимыми.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDPrimaryKey:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


class Timestamps:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


@lru_cache
def get_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        # Параметры запроса не попадают в текст ошибки: там бывают почта и ФИО сотрудника.
        hide_parameters=True,
        connect_args={
            "server_settings": {
                "idle_in_transaction_session_timeout": str(settings.db_idle_in_transaction_ms)
            }
        },
    )


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with get_sessionmaker()() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]

SessionFactory = Callable[[], AsyncSession]


def get_session_factory() -> SessionFactory:
    """Короткие сессии для долгих ответов: поток событий берёт соединение на миг, а не на час."""
    return get_sessionmaker()


SessionFactoryDep = Annotated[SessionFactory, Depends(get_session_factory)]
