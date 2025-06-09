from fastapi import Request, Response, HTTPException, Cookie, Depends, Header
from datetime import datetime
from pyobjectID import PyObjectId
from datetime import datetime
from typing import Annotated
from fastapi.security import HTTPBearer

from db.client import users, user_access, sessions, admins
from db.models.user_access import UserAccess
from db.models.users import User
from db.models.admins import Admin
from db.models.session import Session

security = HTTPBearer()

async def retrieve_session(token: Annotated[str, Depends(security)]):
    session_id = token.credentials

    session_dict = await sessions.find_one({"_id": PyObjectId.to_object(session_id)})
    if session_dict == None: return None

    return Session(**session_dict)

async def validate_session(session: Annotated[Session | None, Depends(retrieve_session)]):
    if session is None:
        raise HTTPException(status_code = 401, detail = "session not found")

    # Is the time from 'expire' setup by the server or mongodb?
    if session.expires < datetime.now() or not session.active: # if chronejob is added to atlas this will not be needed
        raise HTTPException(status_code = 401, detail = "session expired, login again")

    user_access_json = await user_access.find_one({ "user_id": session.user_id })
    if user_access_json is None:
        raise HTTPException(status_code = 500, detail = "user with session not found")

    user_access_instance = UserAccess(**user_access_json)
    if user_access_instance.role == "msb":
        user = User(**(await users.find_one({ "_id": PyObjectId.to_object(user_access_instance.user_id) })))
        return {
            "name": user.name,
            "id": user.id,
            "configuration": user.configuration,
            "role": user_access_instance.role,
        }
    else: # admin 
        admin = Admin(**(await admins.find_one({ "_id": PyObjectId.to_object(user_access_instance.user_id) })))
        return {
            "name": admin.name,
            "id": admin.id,
            "role": user_access_instance.role
        }