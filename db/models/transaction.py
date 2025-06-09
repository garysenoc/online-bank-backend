from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pyobjectID import MongoObjectId
from typing import Optional, Literal

TransactionStatus = Literal["pending", "processing", "completed", "cancelled", "failed"]

class RecipientTransaction(BaseModel):
    fullname: str
    account_number: str
    routing_number: str

class Fee(BaseModel):
    base: float
    priority: float

class Date(BaseModel):
    requested: datetime
    concluded: datetime | None

class Transaction(BaseModel):
    id: Optional[MongoObjectId] = Field(alias = "_id", default = None)
    sender_subaccount: str = Field(alias = "sender")
    recipient: RecipientTransaction = Field(alias = "recipient")
    amount: float
    fee: Fee
    priority: str
    date: Date
    notes: Optional[list[str]] = None
    status: TransactionStatus

    model_config = ConfigDict(populate_by_name = True, arbitrary_types_allowed = True)

# TODO: use the same fields as Transaction
class CreateTransaction(BaseModel):
    senderSubaccount: str
    recipient: RecipientTransaction
    amount: float
    baseFee: float
    priorityFee: float
    priority: str
    note: str

class UpdateTransaction(BaseModel):
    status: TransactionStatus

    model_config = ConfigDict(arbitrary_types_allowed = True)

class DepositTransaction(BaseModel):
    id: Optional[MongoObjectId] = Field(alias = "_id", default = None)
    recipient: str
    amount: float
    status: Optional[str] = Field(default = None)
    type: Optional[str] = Field(default = None)
    date: Optional[datetime] = Field(default = None)

    model_config = ConfigDict(arbitrary_types_allowed = True)