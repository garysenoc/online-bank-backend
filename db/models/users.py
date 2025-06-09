from pydantic import BaseModel, ConfigDict, Field
from pyobjectID import MongoObjectId
from typing import Optional

class Configuration(BaseModel):
    card_deposit: bool

class User(BaseModel):
    id: Optional[MongoObjectId] = Field(alias="_id", default=None)
    name: str
    blocked: bool = False
    configuration: Configuration

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
