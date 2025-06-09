from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pyobjectID import PyObjectId
from typing import Optional

class Session(BaseModel):
    id: Optional[PyObjectId] = Field(alias = "_id", default = None)
    user_id: str
    expires: datetime
    active: bool = Field(default = False)

    model_config = ConfigDict(populate_by_name = True, arbitrary_types_allowed = True)

class Login(BaseModel):
    email: str
    password: str
    

class SessionId(BaseModel):
    session_id: str