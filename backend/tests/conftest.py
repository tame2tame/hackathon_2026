"""Тестовая БД: миграции и демо-данные один раз за сессию, откат после каждого теста."""

import asyncio
import base64
import os
import tempfile
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

import pytest

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://radar:radar@127.0.0.1:55432/radar_test"
)
# Вложения тестов пишутся во временный каталог, а не в рабочий var/uploads.
TEST_UPLOAD_DIR = tempfile.mkdtemp(prefix="radar-uploads-")
# Настройки читаются при первом обращении, поэтому окружение задаётся до импорта приложения.
# Ключ шифрования контактов: фиксированный, чтобы тесты не зависели от окружения машины.
TEST_PD_KEY = base64.urlsafe_b64encode(b"radar-test-key-32-bytes-exactly!").decode()
# Адреса внешних систем в тестах заведомо мёртвые: иначе поднятые на машине заглушки
# (а их поднимают по docs/DEPLOY.md) меняли бы результат тестов отказа. Порт 9 отказывает сразу.
DEAD_URL = "http://127.0.0.1:9"
os.environ.update(
    APP_ENV="test",
    AUTH_MODE="dev",
    DATABASE_URL=TEST_DATABASE_URL,
    UPLOAD_DIR=TEST_UPLOAD_DIR,
    PD_ENCRYPTION_KEY=TEST_PD_KEY,
    LMS_BASE_URL=DEAD_URL,
    SITE_BASE_URL=DEAD_URL,
    TELEGRAM_API_URL=DEAD_URL,
    MAX_API_URL=DEAD_URL,
)

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402

from app.core.cache import get_cache  # noqa: E402
from app.core.db import get_session, get_session_factory  # noqa: E402
from app.demo import seed_demo  # noqa: E402
from app.main import create_app  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parents[1]


async def _seed() -> None:
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        await seed_demo(session, datetime.now(UTC))
        await session.commit()
    await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def database() -> None:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.attributes["database_url"] = TEST_DATABASE_URL
    # Откат до нуля и повторное применение заодно проверяют downgrade миграций.
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    asyncio.run(_seed())


@pytest.fixture(autouse=True)
def cache() -> None:
    """Кэш живёт в памяти процесса, а база откатывается после теста: чистим и его."""
    get_cache.cache_clear()


@pytest.fixture
async def connection() -> AsyncIterator[AsyncConnection]:
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.connect() as conn:
        transaction = await conn.begin()
        yield conn
        await transaction.rollback()
    await engine.dispose()


def _session(connection: AsyncConnection) -> AsyncSession:
    # commit() внутри кода приложения закрывает только точку сохранения, а не внешнюю транзакцию.
    return AsyncSession(
        bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )


@pytest.fixture
async def session(connection: AsyncConnection) -> AsyncIterator[AsyncSession]:
    async with _session(connection) as db_session:
        yield db_session


@pytest.fixture
async def client(connection: AsyncConnection) -> AsyncIterator[AsyncClient]:
    app = create_app()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with _session(connection) as db_session:
            yield db_session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_session_factory] = lambda: lambda: _session(connection)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http
