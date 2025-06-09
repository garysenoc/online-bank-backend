from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from pyobjectID import MongoObjectId
from typing import Annotated

from db.client import transactions, subaccounts
from dependencies.session import validate_session
from db.models.transaction import CreateTransaction, Transaction, Fee, Date, UpdateTransaction, DepositTransaction

router = APIRouter(
    prefix = "/transactions"
)

# TODO: Add skip, limit, and search with text
@router.get("/", status_code=200)
async def get_transactions(session: Annotated[dict, Depends(validate_session)]):
    subaccount_filter_criteria = { "admin_id": session["id"] } if session["role"] == "admin" else { "owner_id": session["id"] }

    subaccounts_ids_raw = await subaccounts.find(subaccount_filter_criteria).to_list()

    subaccounts_ids = [ str(subaccount["_id"]) for subaccount in subaccounts_ids_raw ]

    transactions_raw = await transactions.find({ "$or": [{"sender": { "$in": subaccounts_ids }}, {"recipient": { "$in": subaccounts_ids }}] }).to_list()

    res = []
    for transaction in transactions_raw:
        if "type" in transaction: res += [DepositTransaction(**transaction)]
        else: res += [Transaction(**transaction)] # By default is internal to external

    return res

async def retrieve_transaction(transaction_id: str):
    transaction = await transactions.find_one({"_id": ObjectId(transaction_id)})
    if transaction == None:
         raise HTTPException(status_code = 404, detail = "Transaction not found")
    
    return Transaction(**transaction)

@router.get("/{transaction_id}", status_code = 200)
async def get_transaction(transaction: Annotated[Transaction, Depends(retrieve_transaction)]):
    return transaction

@router.post("/", status_code = 200)
async def post_transaction(payload_tx: CreateTransaction):
    
    tx = Transaction(
		sender_subaccount = payload_tx.senderSubaccount,
		recipient = payload_tx.recipient,
		amount = payload_tx.amount,
        fee = Fee(base = payload_tx.baseFee, priority = payload_tx.priorityFee),
        priority = payload_tx.priority,
        date = Date(requested = datetime.now(timezone.utc), concluded = None),
		notes = ["client: " + payload_tx.note],
        status = "pending"
    )
      
    tx.id = str((await transactions.insert_one(tx.model_dump(by_alias = True, exclude = {"id"}))).inserted_id)
    tx.date.requested = (await transactions.find_one({ '_id': ObjectId(tx.id) }, { 'date.requested': True }))['date']['requested'] # Avoid Date Format Issues

    return tx

@router.post("/complete/{transaction_id}")
async def complete_transaction(transaction: Annotated[Transaction, Depends(retrieve_transaction)], _: Annotated[dict, Depends(validate_session)]):
    await transactions.update_one({'_id': ObjectId(transaction.id)}, {'$set': {'status': 'completed', 'date.concluded': datetime.now(timezone.utc)}})
    await subaccounts.update_one({'_id': ObjectId(transaction.sender_subaccount)}, {'$inc': {"balance.total": -transaction.amount}})


@router.post("/{transaction_id}")
async def update_transaction(transaction: Annotated[Transaction, Depends(retrieve_transaction)], update_transaction: UpdateTransaction, _: Annotated[dict, Depends(validate_session)]):
    transaction.status = update_transaction.status
    await transactions.update_one({'_id': ObjectId(transaction.id)}, {'$set': transaction.model_dump(by_alias = True, exclude = {"id"})})


# Deposit Transactions
@router.post("/deposit/")
async def create_deposit_transaction(payload_deposit_tx: DepositTransaction, _: Annotated[dict, Depends(validate_session)]):
    payload_deposit_tx.status = "completed"
    payload_deposit_tx.type = "deposit"
    payload_deposit_tx.date = datetime.now(timezone.utc)
    
    await subaccounts.update_one({'_id': ObjectId(payload_deposit_tx.recipient)}, {'$inc': { "balance.total": payload_deposit_tx.amount }})
    payload_deposit_tx.id = str((await transactions.insert_one(payload_deposit_tx.model_dump(by_alias = True, exclude = {"id"}))).inserted_id)
    payload_deposit_tx.date = (await transactions.find_one({ '_id': ObjectId(payload_deposit_tx.id) }, { 'date': True }))['date'] # Avoid Date Format Issues
    return payload_deposit_tx