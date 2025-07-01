import pytest
from httpx import AsyncClient

from db.models.subaccount import CreateSubaccount
from db.models.transaction import CreateTransaction


async def create_subaccount(subaccount_payload: CreateSubaccount, async_client: AsyncClient, headers: dict):
    response = await async_client.post("/v1/subaccounts/", json=subaccount_payload, headers=headers)
    return response.json()


async def create_transaction(tx_payload: CreateTransaction, async_client: AsyncClient, headers: dict):
    response = await async_client.post("/v1/transactions/", json=tx_payload, headers=headers)
    return response.json()


@pytest.fixture(autouse=True)
async def created_subaccount(async_client: AsyncClient, headers: dict):
    return await create_subaccount(
        {
            "admin_id": "685efac1afa55d0bad73c6d3",
            "owner_id": "685eed44dd73e20ae1c32c6b",
            "name": "Test SubAcct 1",
            "account_number": "7327205215",
            "routing_number": "490871470",
            "balance": {
                "total": 2500,
                "processing": 0
            }
        },
        async_client,
        headers
    )


@pytest.fixture(autouse=True)
async def created_transaction(async_client: AsyncClient, headers: dict, created_subaccount: dict):
    return await create_transaction(
        {
            "senderSubaccount": created_subaccount["subaccount"],
            "recipient": {
                "fullname": "Test User 1",
                "account_number": "7327205214",
                "routing_number": "490871469"
            },
            "amount": 1000.0,
            "baseFee": 50.0,
            "priorityFee": 50.0,
            "priority": "low",
            "note": "Test Note 1",
        },
        async_client,
        headers
    )


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
        "senderSubaccount": "685efac1afa55d0bad73c6d3",
        "recipient": {
            "fullname": "Test User 1",
            "account_number": "7327205214",
            "routing_number": "490871469"
        },
        "amount": 1000.0,
        "baseFee": 50.0,
        "priorityFee": 50.0,
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
