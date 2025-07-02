import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_get_subaccounts(async_client: AsyncClient, headers: dict, created_subaccount: dict):
    response = await async_client.get("/v1/subaccounts/", headers=headers)
    subaccount_response = await async_client.get(f"/v1/subaccounts/{created_subaccount['subaccount']}", headers=headers)
    subaccount = subaccount_response.json()

    assert response.status_code == 200
    assert response.json() == [subaccount]


@pytest.mark.anyio
async def test_get_subaccount(async_client: AsyncClient, headers: dict, created_subaccount: dict):
    response = await async_client.get(f"/v1/subaccounts/{created_subaccount['subaccount']}", headers=headers)
    subaccount_response = await async_client.get(f"/v1/subaccounts/{created_subaccount['subaccount']}", headers=headers)
    subaccount = subaccount_response.json()

    assert response.status_code == 200
    assert response.json() == subaccount


@pytest.mark.anyio
async def test_create_subaccount(async_client: AsyncClient, headers: dict):
    subaccount_payload = {
        "admin_id": "685efac1afa55d0bad73c6d3",
        "owner_id": "685eed44dd73e20ae1c32c6b",
        "name": "Test SubAcct 1",
        "account_number": "7327205215",
        "routing_number": "490871470",
        "balance": {
            "total": 2500,
            "processing": 0
        }
    }
    response = await async_client.post("/v1/subaccounts/", json=subaccount_payload, headers=headers)
    assert response.status_code == 200


@pytest.mark.anyio
async def test_update_subaccount_balance(async_client: AsyncClient, headers: dict, created_subaccount: dict):
    response = await async_client.post(f"/v1/subaccounts/{created_subaccount['subaccount']}/balance", json={"total": 3000, "processing": 0}, headers=headers)
    subaccount_response = await async_client.get(f"/v1/subaccounts/{created_subaccount['subaccount']}", headers=headers)
    subaccount = subaccount_response.json()

    assert response.status_code == 200
    assert subaccount["balance"]["total"] == 3000
