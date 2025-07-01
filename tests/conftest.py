import os
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from bson import ObjectId
from passlib.hash import bcrypt

from main import app
from dependencies.session import validate_session
from db.client import database


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