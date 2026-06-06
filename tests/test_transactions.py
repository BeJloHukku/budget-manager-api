"""Transactions CRUD smoke tests."""
import pytest


async def _register_and_login(client, api_prefix, email="t@example.com") -> str:
    await client.post(
        f"{api_prefix}/auth/register",
        json={"email": email, "password": "password123"},
    )
    r = await client.post(
        f"{api_prefix}/auth/login",
        data={"username": email, "password": "password123"},
    )
    return r.json()["access_token"]


@pytest.mark.asyncio
async def test_transaction_crud(client, api_prefix):
    token = await _register_and_login(client, api_prefix)
    headers = {"Authorization": f"Bearer {token}"}

    # create
    r = await client.post(
        f"{api_prefix}/transactions",
        headers=headers,
        json={
            "type": "expense",
            "amount": "123.45",
            "description": "Lunch",
            "date": "2026-05-01",
        },
    )
    assert r.status_code == 201, r.text
    txn = r.json()
    assert txn["description"] == "Lunch"
    txn_id = txn["id"]

    # list
    r = await client.get(f"{api_prefix}/transactions", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1

    # filter by type
    r = await client.get(
        f"{api_prefix}/transactions?type=income", headers=headers
    )
    assert r.json()["total"] == 0

    # patch
    r = await client.patch(
        f"{api_prefix}/transactions/{txn_id}",
        headers=headers,
        json={"description": "Dinner", "amount": "200.00"},
    )
    assert r.status_code == 200
    assert r.json()["description"] == "Dinner"

    # get one
    r = await client.get(f"{api_prefix}/transactions/{txn_id}", headers=headers)
    assert r.status_code == 200

    # stats
    r = await client.get(f"{api_prefix}/transactions/stats", headers=headers)
    assert r.status_code == 200
    assert r.json()["expense"] == 200.0

    # delete
    r = await client.delete(f"{api_prefix}/transactions/{txn_id}", headers=headers)
    assert r.status_code == 204

    r = await client.get(f"{api_prefix}/transactions/{txn_id}", headers=headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_default_categories_seeded(client, api_prefix):
    token = await _register_and_login(client, api_prefix, "cats@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    r = await client.get(f"{api_prefix}/categories", headers=headers)
    assert r.status_code == 200
    cats = r.json()
    assert len(cats) >= 5
    assert {c["type"] for c in cats} == {"income", "expense"}


@pytest.mark.asyncio
async def test_user_isolation(client, api_prefix):
    token_a = await _register_and_login(client, api_prefix, "a@example.com")
    token_b = await _register_and_login(client, api_prefix, "b@example.com")

    # user A creates a transaction
    r = await client.post(
        f"{api_prefix}/transactions",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"type": "income", "amount": "1000", "date": "2026-05-01"},
    )
    assert r.status_code == 201
    txn_id = r.json()["id"]

    # user B doesn't see it
    r = await client.get(
        f"{api_prefix}/transactions",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r.json()["total"] == 0

    # user B can't fetch by id
    r = await client.get(
        f"{api_prefix}/transactions/{txn_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r.status_code == 404
