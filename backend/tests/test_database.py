"""Database integration tests — verify session, models, migrations."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.main import app
from app.shared.database import async_session_factory


@pytest.mark.asyncio
async def test_db_session_works():
    """Verify we can create a session and execute raw SQL."""
    async with async_session_factory() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1


@pytest.mark.asyncio
async def test_tables_exist():
    """Verify users and pets tables were created by migration."""
    async with async_session_factory() as session:
        tables = await session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        )
        names = {r[0] for r in tables.fetchall()}
        assert "users" in names
        assert "pets" in names
        assert "alembic_version" in names


@pytest.mark.asyncio
async def test_health_includes_db():
    """Verify the readiness endpoint reports DB status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "database" in data["checks"]
        assert data["checks"]["database"]["status"] == "ok"
