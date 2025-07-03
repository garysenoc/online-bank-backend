import os
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from bson import ObjectId
from passlib.hash import bcrypt

from main import app
from dependencies.session import validate_session
from db.client import database
from db.models.subaccount import CreateSubaccount
from db.models.transaction import CreateTransaction
from db.models.user_access import CreateUserAccess


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def headers():
    return {"Authorization": "Bearer TOKEN"}


@pytest.fixture(autouse=True)
async def clear_collections():
    yield

    if database.name == os.getenv("TEST_DB"):
        collections = ["users", "subaccounts", "transactions", "deposits", "sessions"]
        for collection in collections:
            await database[collection].delete_many({})


async def test_validate_session():
    admin_id = ObjectId("685efac1afa55d0bad73c6d3")
    admin_count = await database["admins"].count_documents({})
    if admin_count == 0:
        await database["admins"].insert_one({
            "_id": admin_id,
            "name": "Admin User"
        })
        await database["user_access"].insert_one({
            "email": "admin@example.com",
            "role": "admin",
            "hashed_password": bcrypt.hash(str(admin_id) + "admin123"),
            "user_id": str(admin_id)
        })

    return {"id": str(admin_id), "role": "admin"}


@pytest.fixture(scope="session")
async def async_client():
    app.dependency_overrides[validate_session] = test_validate_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url=os.getenv("TEST_BASE_URL")) as client:
        yield client

    if database.name == os.getenv("TEST_DB"):
        collections = ["admins", "user_access"]
        for collection in collections:
            await database[collection].delete_many({})


async def create_subaccount(subaccount_payload: CreateSubaccount, async_client: AsyncClient, headers: dict):
    response = await async_client.post("/v1/subaccounts/", json=subaccount_payload, headers=headers)
    return response.json()


async def create_transaction(tx_payload: CreateTransaction, async_client: AsyncClient, headers: dict):
    response = await async_client.post("/v1/transactions/", json=tx_payload, headers=headers)
    return response.json()


async def create_user(user_payload: CreateUserAccess, async_client: AsyncClient, headers: dict):
    response = await async_client.post("/v1/user/", json=user_payload, headers=headers)
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
            "sender_subaccount": created_subaccount["subaccount"],
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
        },
        async_client,
        headers
    )


@pytest.fixture(autouse=True)
async def created_user(async_client: AsyncClient, headers: dict):
    return await create_user(
        {
            "name": "Test User 1",
            "email": "testuser1@example.com",
            "password": "pass123",
        },
        async_client,
        headers
    )
