import pytest
from httpx import AsyncClient

from db.client import deposits
from db.models.payments import CardDeposit


def exclude_keys(data: dict, excluded_list: list):
    return {k: v for k, v in data.items() if k not in excluded_list}


@pytest.mark.anyio
async def test_get_completed_deposits(async_client: AsyncClient, headers: dict, created_subaccount: dict):
    deposit_fields = {
        "recipient_subaccount": created_subaccount["subaccount"],
        "cko_payment_session_id": "cko_test_1234567890",
        "deposit_amount": 100.00,
        "status": "completed",
        "source": {
            "type": "card",
            "card_type": "visa",
            "scheme": "credit",
            "name": "Test User 1",
            "last_4": "1234"
        },
        "date": "2023-10-01T12:00:00Z",
    }

    deposit_instance = CardDeposit(**deposit_fields)
    await deposits.insert_one(deposit_instance.model_dump(exclude={"_id"}))

    response = await async_client.get("/v1/deposits/completed", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.anyio
async def test_get_deposit_by_cko_session_id(async_client: AsyncClient, headers: dict, created_subaccount: dict):
    cko_payment_session_id = "cko_test_1234567890"
    deposit_fields = {
        "recipient_subaccount": created_subaccount["subaccount"],
        "cko_payment_session_id": cko_payment_session_id,
        "deposit_amount": 100.00,
        "status": "completed",
        "source": {
            "type": "card",
            "card_type": "visa",
            "scheme": "credit",
            "name": "Test User 1",
            "last_4": "1234"
        },
        "date": "2023-10-01T12:00:00Z",
    }

    deposit_instance = CardDeposit(**deposit_fields)
    deposit_id = (await deposits.insert_one(deposit_instance.model_dump(exclude={"_id"}))).inserted_id
    deposit = await deposits.find_one({ "_id": deposit_id })

    response = await async_client.get(f"/v1/deposits/{cko_payment_session_id}", headers=headers)
    assert response.status_code == 200
    assert exclude_keys(response.json(), ["_id", "id", "date"]) == exclude_keys(deposit, ["_id", "id", "date"])