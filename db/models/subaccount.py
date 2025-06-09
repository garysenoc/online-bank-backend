from pyobjectID import PyObjectId, MongoObjectId
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class Balance(BaseModel):
    total: int
    processing: int

class Subaccount(BaseModel):
    id: Optional[MongoObjectId] = Field(alias = "_id", default = None)
    admin_id: MongoObjectId
    owner_id: MongoObjectId
    name: str
    routing_number: str
    account_number: str
    balance: Balance

    # TODO: Implement API
    #subaccountType: str
    #api: str

    model_config = ConfigDict(populate_by_name = True, arbitrary_types_allowed = True)

class CreateSubaccount(BaseModel):
    admin_id: str
    owner_id: str
    name: str
    routing_number: str
    account_number: str
    balance: Balance