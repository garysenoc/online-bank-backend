from pydantic import BaseModel, ConfigDict, Field
from pyobjectID import MongoObjectId
from typing import Optional

class Admin(BaseModel):
    id: Optional[MongoObjectId] = Field(alias="_id", default=None)
    name: str

    model_config = ConfigDict(populate_by_name = True, arbitrary_types_allowed = True)
