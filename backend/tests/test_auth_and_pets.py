"""Critical user journey: register, authenticate, and manage a pet."""

from uuid import uuid4

import pytest
from httpx import ASGITransport
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_authenticated_pet_journey():
    email = f"owner-{uuid4()}@example.com"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        registration = await client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "safepassword",
                "display_name": "Owner",
            },
        )
        assert registration.status_code == 201
        login = await client.post(
            "/api/auth/login", json={"email": email, "password": "safepassword"}
        )
        assert login.status_code == 200
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        pet = await client.post(
            "/api/pets", headers=headers, json={"name": "Mochi", "species": "cat"}
        )
        assert pet.status_code == 201
        pet_id = pet.json()["id"]
        feeding = await client.post(
            f"/api/pets/{pet_id}/feedings",
            headers=headers,
            json={"food_type": "dry food", "amount": 35},
        )
        assert feeding.status_code == 201
        dashboard = await client.get("/api/dashboard", headers=headers)
        data = dashboard.json()
        assert data["pets"] == 1
        assert data["feedings"] == 1
        assert data["excretions"] == 0
        assert data["behaviors"] == 0
