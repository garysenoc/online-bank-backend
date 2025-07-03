import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_get_transactions(async_client: AsyncClient, headers: dict, created_transaction: dict):
    response = await async_client.get("/v1/transactions/", headers=headers)
    assert response.status_code == 200
    assert response.json() == [created_transaction]


@pytest.mark.anyio
async def test_get_transaction(async_client: AsyncClient, headers: dict, created_transaction: dict):
    response = await async_client.get(f"/v1/transactions/{created_transaction['_id']}", headers=headers)
    assert response.status_code == 200
    assert response.json() == created_transaction


@pytest.mark.anyio
async def test_create_transaction(async_client: AsyncClient, headers: dict):
    tx_payload = {
        "sender_subaccount": "685efac1afa55d0bad73c6d3",
        "recipient": {
            "fullname": "Test User 1",
            "account_number": "7327205214",
            "routing_number": "490871469"
        },
        "amount": 1000.0,
        "fee": {
            "base": 50.0,
            "priority": 50.0
        },
        "priority": "low",
        "note": "Test Note 1",
    }
    response = await async_client.post("/v1/transactions/", json=tx_payload, headers=headers)
    assert response.status_code == 200


@pytest.mark.anyio
async def test_create_transaction_missing_data(async_client: AsyncClient, headers: dict):
    response = await async_client.post("/v1/transactions/", json={}, headers=headers)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_complete_transaction(async_client: AsyncClient, headers: dict, created_transaction: dict, created_subaccount: dict):
    tx_id = created_transaction["_id"]
    response = await async_client.post(f"/v1/transactions/complete/{tx_id}", json={}, headers=headers)

    assert response.status_code == 200

    tx_response = await async_client.get(f"/v1/transactions/{tx_id}", headers=headers)
    transaction = tx_response.json()
    assert transaction["status"] == "completed"
    assert transaction["date"]["concluded"] is not None

    subaccount_response = await async_client.get(f"/v1/subaccounts/{created_subaccount['subaccount']}", headers=headers)
    subaccount = subaccount_response.json()
    assert subaccount["balance"]["total"] == 1500


@pytest.mark.anyio
async def test_update_transaction(async_client: AsyncClient, headers: dict, created_transaction: dict):
    tx_id = created_transaction["_id"]
    response = await async_client.post(f"/v1/transactions/{tx_id}", json={"status": "failed"}, headers=headers)

    assert response.status_code == 200

    tx_response = await async_client.get(f"/v1/transactions/{tx_id}", headers=headers)
    transaction = tx_response.json()
    assert transaction["status"] == "failed"


@pytest.mark.anyio
async def test_create_deposit_transaction(async_client: AsyncClient, headers: dict, created_subaccount: dict):
    tx_payload = {"recipient": created_subaccount["subaccount"], "amount": 1500.0}
    response = await async_client.post("/v1/transactions/deposit/", json=tx_payload, headers=headers)
    assert response.status_code == 200

    subaccount_response = await async_client.get(f"/v1/subaccounts/{created_subaccount['subaccount']}", headers=headers)
    subaccount = subaccount_response.json()
    assert subaccount["balance"]["total"] == 4000
