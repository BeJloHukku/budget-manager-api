"""Auth flow smoke tests."""
import pytest


@pytest.mark.asyncio
async def test_register_login_me(client, api_prefix):
    # register
    r = await client.post(
        f"{api_prefix}/auth/register",
        json={"email": "u1@example.com", "password": "password123"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["email"] == "u1@example.com"

    # duplicate email -> 409
    r = await client.post(
        f"{api_prefix}/auth/register",
        json={"email": "u1@example.com", "password": "password123"},
    )
    assert r.status_code == 409

    # login
    r = await client.post(
        f"{api_prefix}/auth/login",
        data={"username": "u1@example.com", "password": "password123"},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

    # me
    r = await client.get(
        f"{api_prefix}/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    assert r.json()["email"] == "u1@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password(client, api_prefix):
    await client.post(
        f"{api_prefix}/auth/register",
        json={"email": "u2@example.com", "password": "password123"},
    )
    r = await client.post(
        f"{api_prefix}/auth/login",
        data={"username": "u2@example.com", "password": "wrong"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_unauthorized(client, api_prefix):
    r = await client.get(f"{api_prefix}/auth/me")
    assert r.status_code == 401
