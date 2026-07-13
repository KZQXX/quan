"""Integration tests for record centre — end-to-end flows + boundary conditions.

Covers: Feeding, Excretion, Behavior CRUD cycles; unauthorised / cross-user
        isolation; field validation; date filtering; ownership enforcement.
"""

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from uuid import uuid4

import pytest
from httpx import ASGITransport
from httpx import AsyncClient

from app.main import app


# ── helpers ──────────────────────────────────────────────────────────────────

async def _register_and_login(client: AsyncClient, email: str) -> dict[str, str]:
    """Register a new user, log in, return {token, display_name}."""
    await client.post(
        "/api/auth/register",
        json={"email": email, "password": "safe12345", "display_name": "Tester"},
    )
    resp = await client.post(
        "/api/auth/login", json={"email": email, "password": "safe12345"}
    )
    data = resp.json()
    return {"token": data["access_token"], "display_name": data["user"]["display_name"]}


async def _create_pet(client: AsyncClient, token: str, name: str = "Mochi") -> str:
    resp = await client.post(
        "/api/pets",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": name, "species": "cat"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


# ── Feeding CRUD cycle ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_feeding_full_crud_cycle():
    email = f"feeding-crud-{uuid4()}@test.com"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        auth = await _register_and_login(client, email)
        headers = {"Authorization": f"Bearer {auth['token']}"}
        pet_id = await _create_pet(client, auth["token"])

        # Create
        create = await client.post(
            f"/api/pets/{pet_id}/feedings",
            headers=headers,
            json={"food_type": "dry food", "amount": 80, "notes": "morning meal"},
        )
        assert create.status_code == 201
        body = create.json()
        record_id = body["id"]
        assert body["food_type"] == "dry food"
        assert body["amount"] == 80
        assert body["notes"] == "morning meal"
        assert body["source"] == "manual"
        assert body["pet_id"] == pet_id

        # Read by id
        get_one = await client.get(
            f"/api/pets/{pet_id}/feedings/{record_id}", headers=headers
        )
        assert get_one.status_code == 200
        assert get_one.json()["id"] == record_id

        # List
        lst = await client.get(f"/api/pets/{pet_id}/feedings", headers=headers)
        assert lst.status_code == 200
        assert len(lst.json()) == 1

        # Update
        patch = await client.patch(
            f"/api/pets/{pet_id}/feedings/{record_id}",
            headers=headers,
            json={"amount": 120, "notes": "extra portion"},
        )
        assert patch.status_code == 200
        assert patch.json()["amount"] == 120
        assert patch.json()["notes"] == "extra portion"
        # untouched field stays
        assert patch.json()["food_type"] == "dry food"

        # Delete
        delete = await client.delete(
            f"/api/pets/{pet_id}/feedings/{record_id}", headers=headers
        )
        assert delete.status_code == 204

        # Verify gone
        verify = await client.get(
            f"/api/pets/{pet_id}/feedings/{record_id}", headers=headers
        )
        assert verify.status_code == 404

        # Dashboard reflects deletion
        dash = await client.get("/api/dashboard", headers=headers)
        assert dash.json()["feedings"] == 0


# ── Excretion CRUD cycle ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_excretion_full_crud_cycle():
    email = f"excretion-crud-{uuid4()}@test.com"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        auth = await _register_and_login(client, email)
        headers = {"Authorization": f"Bearer {auth['token']}"}
        pet_id = await _create_pet(client, auth["token"])

        create = await client.post(
            f"/api/pets/{pet_id}/excretions",
            headers=headers,
            json={"type": "normal", "consistency": "solid", "notes": "afternoon"},
        )
        assert create.status_code == 201
        record_id = create.json()["id"]

        # Update
        patch = await client.patch(
            f"/api/pets/{pet_id}/excretions/{record_id}",
            headers=headers,
            json={"consistency": "soft"},
        )
        assert patch.status_code == 200
        assert patch.json()["consistency"] == "soft"
        assert patch.json()["type"] == "normal"

        # Delete
        await client.delete(
            f"/api/pets/{pet_id}/excretions/{record_id}", headers=headers
        )
        verify = await client.get(
            f"/api/pets/{pet_id}/excretions/{record_id}", headers=headers
        )
        assert verify.status_code == 404


# ── Behavior CRUD cycle ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_behavior_full_crud_cycle():
    email = f"behavior-crud-{uuid4()}@test.com"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        auth = await _register_and_login(client, email)
        headers = {"Authorization": f"Bearer {auth['token']}"}
        pet_id = await _create_pet(client, auth["token"])

        create = await client.post(
            f"/api/pets/{pet_id}/behaviors",
            headers=headers,
            json={
                "behavior_type": "playing",
                "duration_minutes": 15,
                "mood": "happy",
                "notes": "chasing toy",
            },
        )
        assert create.status_code == 201
        record_id = create.json()["id"]

        # Update only mood
        patch = await client.patch(
            f"/api/pets/{pet_id}/behaviors/{record_id}",
            headers=headers,
            json={"mood": "excited"},
        )
        assert patch.status_code == 200
        assert patch.json()["mood"] == "excited"
        assert patch.json()["behavior_type"] == "playing"

        # Delete
        await client.delete(
            f"/api/pets/{pet_id}/behaviors/{record_id}", headers=headers
        )
        verify = await client.get(
            f"/api/pets/{pet_id}/behaviors/{record_id}", headers=headers
        )
        assert verify.status_code == 404


# ── Unauthorised access (no token) ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_records_reject_unauthenticated_access():
    email = f"unauth-{uuid4()}@test.com"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        auth = await _register_and_login(client, email)
        headers = {"Authorization": f"Bearer {auth['token']}"}
        pet_id = await _create_pet(client, auth["token"])

        # Create a record to have a real id
        resp = await client.post(
            f"/api/pets/{pet_id}/feedings",
            headers=headers,
            json={"food_type": "snack"},
        )
        record_id = resp.json()["id"]

        no_auth = {}  # no headers at all

        # Every record endpoint must return 401 / 403 when unauthenticated
        for verb, url in [
            ("GET", f"/api/pets/{pet_id}/feedings"),
            ("POST", f"/api/pets/{pet_id}/feedings"),
            ("GET", f"/api/pets/{pet_id}/feedings/{record_id}"),
            ("PATCH", f"/api/pets/{pet_id}/feedings/{record_id}"),
            ("DELETE", f"/api/pets/{pet_id}/feedings/{record_id}"),
        ]:
            method = getattr(client, verb.lower())
            r = await method(url, headers=no_auth)
            assert r.status_code == 401, f"{verb} {url} should return 401, got {r.status_code}"


# ── Cross-user isolation ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cross_user_isolation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # User A
        auth_a = await _register_and_login(client, f"alice-{uuid4()}@test.com")
        pet_a = await _create_pet(client, auth_a["token"])
        resp = await client.post(
            f"/api/pets/{pet_a}/feedings",
            headers={"Authorization": f"Bearer {auth_a['token']}"},
            json={"food_type": "wet food"},
        )
        feeding_a = resp.json()["id"]

        # User B
        auth_b = await _register_and_login(client, f"bob-{uuid4()}@test.com")
        pet_b = await _create_pet(client, auth_b["token"])

        headers_b = {"Authorization": f"Bearer {auth_b['token']}"}

        # B cannot access A's pet records
        assert (
            await client.get(f"/api/pets/{pet_a}/feedings", headers=headers_b)
        ).status_code == 404
        assert (
            await client.get(f"/api/pets/{pet_a}/feedings/{feeding_a}", headers=headers_b)
        ).status_code == 404
        assert (
            await client.patch(
                f"/api/pets/{pet_a}/feedings/{feeding_a}",
                headers=headers_b,
                json={"amount": 999},
            )
        ).status_code == 404
        assert (
            await client.delete(f"/api/pets/{pet_a}/feedings/{feeding_a}", headers=headers_b)
        ).status_code == 404

        # B's own pet still works as normal
        own = await client.post(
            f"/api/pets/{pet_b}/feedings",
            headers=headers_b,
            json={"food_type": "treat"},
        )
        assert own.status_code == 201

        # Dashboard only counts own data
        dash = await client.get("/api/dashboard", headers=headers_b)
        assert dash.json() == {"pets": 1, "feedings": 1, "excretions": 0, "behaviors": 0}


# ── Validation (422) ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_validation_errors():
    email = f"validation-{uuid4()}@test.com"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        auth = await _register_and_login(client, email)
        headers = {"Authorization": f"Bearer {auth['token']}"}
        pet_id = await _create_pet(client, auth["token"])

        # Missing required field
        resp = await client.post(
            f"/api/pets/{pet_id}/feedings", headers=headers, json={"amount": 50}
        )
        assert resp.status_code == 422

        # Empty food_type
        resp = await client.post(
            f"/api/pets/{pet_id}/feedings",
            headers=headers,
            json={"food_type": "", "amount": 50},
        )
        assert resp.status_code == 422

        # Negative amount
        resp = await client.post(
            f"/api/pets/{pet_id}/feedings",
            headers=headers,
            json={"food_type": "kibble", "amount": -5},
        )
        assert resp.status_code == 422

        # Excretion missing type
        resp = await client.post(
            f"/api/pets/{pet_id}/excretions",
            headers=headers,
            json={"consistency": "solid"},
        )
        assert resp.status_code == 422

        # Behavior missing behavior_type
        resp = await client.post(
            f"/api/pets/{pet_id}/behaviors",
            headers=headers,
            json={"duration_minutes": 10},
        )
        assert resp.status_code == 422

        # Behavior negative duration
        resp = await client.post(
            f"/api/pets/{pet_id}/behaviors",
            headers=headers,
            json={"behavior_type": "sleeping", "duration_minutes": -1},
        )
        assert resp.status_code == 422


# ── Date-range filtering ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_date_range_filtering():
    email = f"datefilter-{uuid4()}@test.com"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        auth = await _register_and_login(client, email)
        headers = {"Authorization": f"Bearer {auth['token']}"}
        pet_id = await _create_pet(client, auth["token"])

        now = datetime.now(timezone.utc)

        # Record from 7 days ago
        await client.post(
            f"/api/pets/{pet_id}/feedings",
            headers=headers,
            json={
                "food_type": "old kibble",
                "recorded_at": (now - timedelta(days=7)).isoformat(),
            },
        )
        # Record from yesterday
        await client.post(
            f"/api/pets/{pet_id}/feedings",
            headers=headers,
            json={
                "food_type": "yesterday snack",
                "recorded_at": (now - timedelta(days=1)).isoformat(),
            },
        )
        # Record from today
        await client.post(
            f"/api/pets/{pet_id}/feedings",
            headers=headers,
            json={
                "food_type": "today breakfast",
                "recorded_at": now.isoformat(),
            },
        )

        # Filter to last 2 days — should return 2
        recent = await client.get(
            f"/api/pets/{pet_id}/feedings",
            headers=headers,
            params={
                "start_date": (now - timedelta(days=2)).isoformat(),
                "end_date": (now + timedelta(hours=1)).isoformat(),
            },
        )
        assert recent.status_code == 200
        assert len(recent.json()) == 2

        # Filter to 8 days ago — should return 1
        old = await client.get(
            f"/api/pets/{pet_id}/feedings",
            headers=headers,
            params={
                "start_date": (now - timedelta(days=8)).isoformat(),
                "end_date": (now - timedelta(days=6)).isoformat(),
            },
        )
        assert old.status_code == 200
        assert len(old.json()) == 1
        assert old.json()[0]["food_type"] == "old kibble"

        # No results in far future
        empty = await client.get(
            f"/api/pets/{pet_id}/feedings",
            headers=headers,
            params={
                "start_date": (now + timedelta(days=30)).isoformat(),
                "end_date": (now + timedelta(days=60)).isoformat(),
            },
        )
        assert empty.status_code == 200
        assert len(empty.json()) == 0


# ── Multiple records and dashboard counts ────────────────────────────────────

@pytest.mark.asyncio
async def test_dashboard_counts_are_accurate():
    email = f"dashcounts-{uuid4()}@test.com"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        auth = await _register_and_login(client, email)
        headers = {"Authorization": f"Bearer {auth['token']}"}
        pet_id = await _create_pet(client, auth["token"], "Luna")

        # Two feedings
        await client.post(
            f"/api/pets/{pet_id}/feedings",
            headers=headers,
            json={"food_type": "breakfast", "amount": 100},
        )
        await client.post(
            f"/api/pets/{pet_id}/feedings",
            headers=headers,
            json={"food_type": "dinner", "amount": 120},
        )

        # Three excretions
        for _ in range(3):
            await client.post(
                f"/api/pets/{pet_id}/excretions",
                headers=headers,
                json={"type": "normal"},
            )

        # One behavior
        await client.post(
            f"/api/pets/{pet_id}/behaviors",
            headers=headers,
            json={"behavior_type": "walking", "duration_minutes": 30},
        )

        dash = await client.get("/api/dashboard", headers=headers)
        assert dash.json() == {"pets": 1, "feedings": 2, "excretions": 3, "behaviors": 1}


# ── 404 for non-existent record id ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_nonexistent_record_returns_404():
    email = f"nonexistent-{uuid4()}@test.com"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        auth = await _register_and_login(client, email)
        headers = {"Authorization": f"Bearer {auth['token']}"}
        pet_id = await _create_pet(client, auth["token"])
        fake_id = str(uuid4())

        assert (
            await client.get(f"/api/pets/{pet_id}/feedings/{fake_id}", headers=headers)
        ).status_code == 404
        assert (
            await client.patch(
                f"/api/pets/{pet_id}/feedings/{fake_id}",
                headers=headers,
                json={"amount": 50},
            )
        ).status_code == 404


# ── Recorded_at override ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_custom_recorded_at():
    email = f"customtime-{uuid4()}@test.com"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        auth = await _register_and_login(client, email)
        headers = {"Authorization": f"Bearer {auth['token']}"}
        pet_id = await _create_pet(client, auth["token"])

        custom_time = "2025-12-25T08:30:00Z"
        resp = await client.post(
            f"/api/pets/{pet_id}/feedings",
            headers=headers,
            json={"food_type": "christmas dinner", "recorded_at": custom_time},
        )
        assert resp.status_code == 201
        # ISO 8601 comparison (both are in UTC)
        assert resp.json()["recorded_at"].startswith("2025-12-25T08:30:00")
