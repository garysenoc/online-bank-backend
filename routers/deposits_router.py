from fastapi import APIRouter, Depends, HTTPException
from pyobjectID import PyObjectId
from typing import Annotated

from db.client import deposits
from db.models.payments import CardDeposit
from dependencies.session import validate_session
from routers.subaccounts_router import get_subaccounts_array_id

router = APIRouter(
  prefix = "/deposits"
)

@router.get("/completed", status_code = 200)
async def get_deposits_completed(session: Annotated[dict, Depends(validate_session)]):
  subaccounts_id = await get_subaccounts_array_id(session)

  deposits_raw = await deposits.find({'recipient_subaccount': {"$in": subaccounts_id}, 'status': 'completed'}).to_list()
  card_deposits = [CardDeposit(**deposit_raw) for deposit_raw in deposits_raw]

  return card_deposits

@router.get("/{cko_payment_session_id}", status_code = 200)
async def get_deposit_by_cko_session_id(cko_payment_session_id: str, session: Annotated[dict, Depends(validate_session)]):
  deposit_raw = await deposits.find_one({'cko_payment_session_id': cko_payment_session_id})
  
  if deposit_raw is None:
    raise HTTPException(status_code = 404, detail="Payment not found")
  
  subaccounts_id = await get_subaccounts_array_id(session)
  if not deposit_raw['recipient_subaccount'] in subaccounts_id:
    raise HTTPException(status_code = 401, detail = "You don't have permission to access this payment. Calling the cops.")

  print(deposit_raw)
  if deposit_raw['status'] == 'completed':
    return CardDeposit(**deposit_raw)