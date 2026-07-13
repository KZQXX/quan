"""Test database setup for asynchronous endpoint tests."""

import pytest_asyncio

import app.models  # noqa: F401
from app.shared.database import Base
from app.shared.database import engine


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_schema():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
