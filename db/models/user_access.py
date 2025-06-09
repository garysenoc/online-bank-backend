from pydantic import BaseModel, ConfigDict, Field
from bson import ObjectId
from typing import Optional
from pyobjectID import MongoObjectId, PyObjectId

class UserAccess(BaseModel):
    id: Optional[MongoObjectId] = Field(alias = "_id", default = None)
    email: str
    role: str
    hashed_password: str
    user_id: str

    model_config = ConfigDict(populate_by_name = True, arbitrary_types_allowed = True)

class CreateUserAccess(BaseModel):
    email: str
    password: str
    name: str

# class UpdateUser(BaseModel):
#     id: str
#     name: Optional[str] = Field(default="")
#     email: Optional[str] = Field(default="")
#     password: Optional[str] = Field(default="")

#class DeleteUserAccess(BaseModel):
#    id:str