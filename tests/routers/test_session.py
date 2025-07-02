import pytest
from httpx import AsyncClient
from pyobjectID import PyObjectId

from db.client import sessions


@pytest.mark.anyio
async def test_get_user_session(async_client: AsyncClient, headers: dict):
    response = await async_client.get("/v1/session/user", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"id": "685efac1afa55d0bad73c6d3", "role": "admin"}


@pytest.mark.anyio
async def test_login(async_client: AsyncClient, headers: dict):
    login_payload = {
        "email": "admin@example.com",
        "password": "admin123",
    }
    response = await async_client.post("/v1/session/login", json=login_payload, headers=headers)
    assert response.status_code == 200


@pytest.mark.anyio
async def test_logout(async_client: AsyncClient, headers: dict):
    login_response = await async_client.post("/v1/session/login", json={
        "email": "admin@example.com",
        "password": "admin123",
    })
    login = login_response.json()
    logout_response = await async_client.post("/v1/session/logout", headers={"Authorization": f"Bearer {login['session_id']}"})
    session = await sessions.find_one({ "_id": PyObjectId.to_object(login["session_id"]) })

    assert login_response.status_code == 200
    assert logout_response.status_code == 200
    assert session["active"] is False