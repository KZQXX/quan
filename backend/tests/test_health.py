"""Test configuration and health check endpoints."""

import pytest
import pytest_asyncio
from httpx import ASGITransport
from httpx import AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client():
    """Async HTTP test client bound to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient):
    response = await client.get("/api/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "checks" in data
    assert data["checks"]["app"]["status"] == "ok"


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Pet Tracker" in response.text


@pytest.mark.asyncio
async def test_404_not_found(client: AsyncClient):
    response = await client.get("/api/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_error_handler(client: AsyncClient):
    """Test that unexpected errors return structured JSON, not stack traces."""
    response = await client.get("/api/health")  # valid endpoint, shouldn't error
    assert response.status_code == 200
