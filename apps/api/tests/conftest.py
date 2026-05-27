from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config.settings import settings
from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app
from app.services.parameter_definition_seed import seed_parameter_definitions
from app.services.test_type_seed import seed_test_types


_MISSING = object()


def require_test_database_url(value: str | None | object = _MISSING) -> str:
    test_database_url = settings.test_database_url if value is _MISSING else value
    if not test_database_url:
        raise RuntimeError("TEST_DATABASE_URL is required to run backend tests safely.")
    if "test" not in test_database_url.lower():
        raise RuntimeError("Refusing to reset database because TEST_DATABASE_URL does not look like a test database.")
    return test_database_url


@pytest.fixture(scope="session")
def test_database_url() -> str:
    return require_test_database_url()


@pytest_asyncio.fixture(autouse=True)
async def test_session_factory(test_database_url: str):
    test_engine = create_async_engine(test_database_url, pool_pre_ping=True, poolclass=NullPool)
    TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)

    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        await seed_test_types(session)
        await seed_parameter_definitions(session)
        await session.commit()

    async def override_get_db_session() -> AsyncIterator[AsyncSession]:
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session

    yield TestSessionLocal

    app.dependency_overrides.pop(get_db_session, None)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client


@pytest_asyncio.fixture
async def db_session(test_session_factory) -> AsyncIterator[AsyncSession]:
    async with test_session_factory() as session:
        yield session
