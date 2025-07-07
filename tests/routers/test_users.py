import pytest
from httpx import AsyncClient


def exclude_keys(data: dict, excluded_list: list):
    return {k: v for k, v in data.items() if k not in excluded_list}


@pytest.mark.anyio
async def test_get_users(async_client: AsyncClient, headers: dict, created_user: dict):
    response = await async_client.get("/v1/user/", headers=headers)
    assert response.status_code == 200
    assert [exclude_keys(user, ["_id"]) for user in response.json()["items"]] == [exclude_keys(created_user, ["_id"])]


@pytest.mark.anyio
async def test_create_user(async_client: AsyncClient, headers: dict):
    user_payload = {
        "name": "Test User 1",
        "email": "testuser1@example.com",
        "password": "pass123",
    }
    response = await async_client.post("/v1/user/", json=user_payload, headers=headers)
    assert response.status_code == 201
    return response.json()