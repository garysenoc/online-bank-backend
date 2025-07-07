import pytest
import random
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone

from db.client import database, transactions
from db.models.transaction import Transaction


async def create_test_subaccounts(async_client: AsyncClient, headers: dict, num: int = 2):
    subaccounts_list = []
    for i in range(num):
        subaccount_data = {
            "admin_id": "685efac1afa55d0bad73c6d3",
            "owner_id": "685eed44dd73e20ae1c32c6b",
            "name": f"Test SubAcct {i + 2}",
            "account_number": "".join([str(random.randint(0, 9)) for _ in range(10)]),
            "routing_number": "".join([str(random.randint(0, 9)) for _ in range(9)]),
            "balance": {
                "total": random.randint(1000, 10000),
                "processing": 0
            }
        }
        subaccounts_list.append(subaccount_data)
    return await database["subaccounts"].insert_many(subaccounts_list)


async def create_test_transactions(sender: str, idx: int, async_client: AsyncClient, headers: dict, num: int = 5):
    transactions_list = []
    for i in range(num):
        transaction_data = {
            "sender_subaccount": sender,
            "recipient": {
                "fullname": f"Test User {(i + 2) * idx}",
                "account_number": "".join([str(random.randint(0, 9)) for _ in range(10)]),
                "routing_number": "".join([str(random.randint(0, 9)) for _ in range(9)]),
            },
            "amount": random.randint(1000, 10000),
            "fee": {
                "base": random.randint(50, 100),
                "priority": random.randint(50, 100)
            },
            "priority": random.choice(["low", "medium", "high"]),
            "date": {
                "requested": datetime.now(timezone.utc) - timedelta(days=random.randint(0, 5)),
                "concluded": None
            },
            "notes": [f"Test Note {(i + 2) * idx}"],
            "status": random.choice(["pending", "processing", "completed", "cancelled", "failed"])
        }
        transactions_list.append(transaction_data)
    return await database["transactions"].insert_many(transactions_list)


@pytest.mark.anyio
async def test_get_transactions(async_client: AsyncClient, headers: dict, created_transaction: dict):
    response = await async_client.get("/v1/transactions/", headers=headers)
    assert response.status_code == 200
    assert response.json()["items"] == [created_transaction]


@pytest.mark.anyio
async def test_get_transactions_with_skip(async_client: AsyncClient, headers: dict):
    subaccount_id1, subaccount_id2 = (await create_test_subaccounts(async_client=async_client, headers=headers)).inserted_ids
    test_transactions1 = await create_test_transactions(sender=str(subaccount_id1), idx=1, async_client=async_client, headers=headers)
    test_transactions2 = await create_test_transactions(sender=str(subaccount_id2), idx=2, async_client=async_client, headers=headers)

    tx2_objects = [Transaction(**tx) for tx in await transactions.find({ "_id": { "$in": test_transactions2.inserted_ids}}).to_list()]

    response = await async_client.get("/v1/transactions/?skip=6", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 5
    assert [Transaction(**tx) for tx in response.json()["items"]] == tx2_objects


@pytest.mark.anyio
async def test_get_transactions_with_limit(async_client: AsyncClient, headers: dict, created_transaction: dict):
    subaccount_id1, subaccount_id2 = (await create_test_subaccounts(async_client=async_client, headers=headers)).inserted_ids
    test_transactions1 = await create_test_transactions(sender=str(subaccount_id1), idx=1, async_client=async_client, headers=headers)
    test_transactions2 = await create_test_transactions(sender=str(subaccount_id2), idx=2, async_client=async_client, headers=headers)

    tx1_objects = [Transaction(**tx) for tx in await transactions.find({ "_id": { "$in": test_transactions1.inserted_ids}}).to_list()]

    response = await async_client.get("/v1/transactions/?limit=6", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 6
    assert [Transaction(**tx) for tx in response.json()["items"]] == [Transaction(**created_transaction)] + tx1_objects


@pytest.mark.anyio
async def test_get_transactions_with_search(async_client: AsyncClient, headers: dict):
    subaccount_id1, subaccount_id2 = (await create_test_subaccounts(async_client=async_client, headers=headers)).inserted_ids
    test_transactions1 = await create_test_transactions(sender=str(subaccount_id1), idx=1, async_client=async_client, headers=headers)
    test_transactions2 = await create_test_transactions(sender=str(subaccount_id2), idx=2, async_client=async_client, headers=headers)

    tx1_objects = [Transaction(**tx) for tx in await transactions.find({ "_id": { "$in": test_transactions1.inserted_ids}}).to_list()]

    response = await async_client.get(f"/v1/transactions/?search={subaccount_id1}", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 5
    assert [Transaction(**tx) for tx in response.json()["items"]] == tx1_objects


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
