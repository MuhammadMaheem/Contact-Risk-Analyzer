import pytest

pytestmark = pytest.mark.asyncio


async def test_register_creates_user(client):
    response = await client.post(
        "/api/auth/register",
        json={"email": "new@test.com", "password": "password123", "full_name": "New User"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@test.com"
    assert body["role"] == "user"


async def test_register_duplicate_email_conflicts(client):
    payload = {"email": "dup@test.com", "password": "password123", "full_name": "Dup User"}
    first = await client.post("/api/auth/register", json=payload)
    assert first.status_code == 201
    second = await client.post("/api/auth/register", json=payload)
    assert second.status_code == 409


async def test_login_wrong_password_rejected(client):
    await client.post(
        "/api/auth/register",
        json={"email": "wrongpass@test.com", "password": "correctpassword", "full_name": "User"},
    )
    response = await client.post(
        "/api/auth/login", json={"email": "wrongpass@test.com", "password": "incorrect"}
    )
    assert response.status_code == 401


async def test_login_returns_usable_token(client):
    await client.post(
        "/api/auth/register",
        json={"email": "tokentest@test.com", "password": "password123", "full_name": "User"},
    )
    login = await client.post(
        "/api/auth/login", json={"email": "tokentest@test.com", "password": "password123"}
    )
    token = login.json()["access_token"]
    me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "tokentest@test.com"


async def test_admin_only_endpoint_rejects_regular_user(client, auth_headers):
    response = await client.get("/api/admin/users", headers=auth_headers)
    assert response.status_code == 403


async def test_unauthenticated_request_rejected(client):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401
