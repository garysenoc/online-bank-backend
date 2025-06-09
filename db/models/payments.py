from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pyobjectID import MongoObjectId

from typing import Optional

class InitiateCardDepositInfo(BaseModel):
  recipient_subaccount: MongoObjectId
  deposit_amount: float

class ProcessingCardDeposit(BaseModel):
  id: Optional[MongoObjectId] = Field(alias = "_id", default = None)
  recipient_subaccount: MongoObjectId
  cko_payment_session_id: str
  deposit_amount: float
  status: str # processing, failed, completed

class SourceCardDeposit(BaseModel):
  type: str
  card_type: str
  scheme: str
  name: str
  last_4: str

class CardDeposit(ProcessingCardDeposit):
  source: SourceCardDeposit
  date: datetime