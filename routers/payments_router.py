import requests
import os
import hashlib
import hmac
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Header, Request, HTTPException, Body
from pyobjectID import PyObjectId
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, timezone

from dependencies.session import validate_session
from db.client import deposits, subaccounts
from db.models.payments import InitiateCardDepositInfo, ProcessingCardDeposit, CardDeposit, SourceCardDeposit

router = APIRouter(
  prefix = "/payments"
)

load_dotenv()

@router.post('/initiate-card-deposit', status_code = 200)
async def initiate_card_deposit(initiate_card_desposit_info: InitiateCardDepositInfo, _: Annotated[dict, Depends(validate_session)]):    
	
	# Initiate Payment
	cko_secret_key = os.environ['CKO_SECRET_KEY']
	headers = { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + cko_secret_key }

	data = {
		'amount': initiate_card_desposit_info.deposit_amount * 100, # dollars to cents
		'currency': 'USD',
		'billing': {
			'address': {
				'country': 'US'
			}
		},
		'success_url': 'https://originaltech.xyz',
		'failure_url': 'https://originaltech.xyz',
		'description': 'Deposit into Original Bank Account',
		'billing_descriptor': {
			'name': 'Deposit Original',
			'city': 'Montana'  
		},
		'enabled_payment_methods': ['card'],
		'processing_channel_id': os.environ['CKO_PAYMENT_PROCESSING_ID']
	}

	r = requests.post('https://api.sandbox.checkout.com/payment-sessions', headers = headers, json = data)
	payment_session = r.json()

	processing_card_deposit = ProcessingCardDeposit(
		recipient_subaccount = initiate_card_desposit_info.recipient_subaccount,
		cko_payment_session_id = payment_session['id'],
		deposit_amount = initiate_card_desposit_info.deposit_amount,
		status = "processing"
	)

	await deposits.insert_one(processing_card_deposit.model_dump(by_alias = True, exclude = {"id"}))
	
	return payment_session

class MetadataPaymentApproved(BaseModel):
	cko_payment_session_id: str

class DataPaymentAprroved(BaseModel):
	metadata: MetadataPaymentApproved
	source: SourceCardDeposit

class PaymentApproved(BaseModel):
	data: DataPaymentAprroved

	model_config = ConfigDict(populate_by_name = True, arbitrary_types_allowed = True)
	

# Add Webhook Sessions - Don't allow anyone to post
@router.post('/webhook', status_code = 200)
async def webhook(request: Request, cko_signature: Annotated[str, Header()], type: Annotated[str, Body(embed = True)]):

	# HMAC Verification
	signature_key = '3f082f99-71b0-4fd0-b4be-44b567cbe9d7'
	body = await request.body()
	hash_instance = hashlib.sha256()
	hash_instance.update(body)
	hmac_instance = hmac.new(bytes(signature_key, encoding = 'utf-8'), body, hashlib.sha256)

	valid_webhook = hmac.compare_digest(hmac_instance.hexdigest(), cko_signature)

	if not valid_webhook:
		raise HTTPException(status_code = 403, detail = "Integration verificaion failed; HMACs don't match.") 

	body = await request.body()
	if type == 'payment_approved':
		payment_approved = PaymentApproved.model_validate_json(body)
		card_deposit_raw = await deposits.find_one({ 'cko_payment_session_id': payment_approved.data.metadata.cko_payment_session_id })
		card_deposit = CardDeposit(**card_deposit_raw, source = payment_approved.data.source, date = datetime.now(timezone.utc))
		card_deposit.status = 'completed'
		
		await deposits.replace_one({'_id': PyObjectId.to_object(card_deposit.id)}, card_deposit.model_dump(by_alias = True, exclude = {"id"}))
		await subaccounts.update_one({'_id': PyObjectId.to_object(card_deposit.recipient_subaccount)}, {'$inc': {'balance.total': card_deposit.deposit_amount}})

	return