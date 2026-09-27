"""Схема из миграций совпадает со схемой из моделей — вплоть до условий индексов и CHECK.

`alembic check` сравнивает столбцы и типы, но не видит, если в миграции у частичного индекса
другое условие или у CHECK другой текст. Поэтому здесь строятся обе схемы и сравниваются
по каталогу PostgreSQL.
"""

from collections.abc import AsyncIterator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine
from sqlalchemy.pool import NullPool

from app.models import Base
from tests.conftest import TEST_DATABASE_URL

CHECK_DB = "radar_models_check"

INDEXES = text(
    "SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname = 'public' "
    "AND tablename <> 'alembic_version'"
)
CONSTRAINTS = text(
    "SELECT rel.relname, con.conname, pg_get_constraintdef(con.oid) "
    "FROM pg_constraint con JOIN pg_class rel ON rel.oid = con.conrelid "
    "JOIN pg_namespace ns ON ns.oid = rel.relnamespace "
    "WHERE ns.nspname = 'public' AND rel.relname <> 'alembic_version'"
)


def _url(database: str) -> str:
    return TEST_DATABASE_URL.rsplit("/", 1)[0] + f"/{database}"


async def _catalog(connection: AsyncConnection) -> set[tuple[str, ...]]:
    indexes = {("index", *row) for row in (await connection.execute(INDEXES)).tuples()}
    constraints = {("constraint", *row) for row in (await connection.execute(CONSTRAINTS)).tuples()}
    return indexes | constraints


@pytest.fixture
async def models_schema() -> AsyncIterator[set[tuple[str, ...]]]:
    admin = create_async_engine(_url("postgres"), poolclass=NullPool, isolation_level="AUTOCOMMIT")
    async with admin.connect() as connection:
        await connection.execute(text(f"DROP DATABASE IF EXISTS {CHECK_DB}"))
        await connection.execute(text(f"CREATE DATABASE {CHECK_DB}"))
    engine = create_async_engine(_url(CHECK_DB), poolclass=NullPool)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with engine.connect() as connection:
            yield await _catalog(connection)
    finally:
        await engine.dispose()
        async with admin.connect() as connection:
            await connection.execute(text(f"DROP DATABASE IF EXISTS {CHECK_DB}"))
        await admin.dispose()


async def test_migrations_build_the_same_schema_as_models(
    connection: AsyncConnection, models_schema: set[tuple[str, ...]]
) -> None:
    migrations_schema = await _catalog(connection)

    only_migrations = sorted(migrations_schema - models_schema)
    only_models = sorted(models_schema - migrations_schema)
    assert not only_migrations, f"Есть только в миграциях: {only_migrations}"
    assert not only_models, f"Есть только в моделях: {only_models}"
