from fastapi import APIRouter, HTTPException, Depends
from pyobjectID import MongoObjectId
from passlib.hash import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Annotated

from dependencies.session import validate_session, retrieve_session
from db.client import user_access, sessions
from db.models.session import Login, Session
from db.models.users import User
from db.models.user_access import UserAccess

router = APIRouter(
    prefix = "/session"
)

@router.get('/user')
async def user(session: Annotated[dict, Depends(validate_session)]):
    return session
    

@router.post('/login', status_code = 200)
async def login(login: Login):

    user_access_res = await user_access.find_one({ "email": login.email })
    if user_access_res is None:
        raise HTTPException(status_code = 404, detail = "Email not found.")
    
    user_access_inst = UserAccess(**user_access_res)

    if not bcrypt.verify(str(user_access_inst.user_id) + login.password, user_access_inst.hashed_password):
        raise HTTPException(status_code = 401, detail = "Incorrect password.")
    
    expires = datetime.now(timezone.utc) + timedelta(days = 30)

    session = Session(user_id = user_access_inst.user_id, expires = expires, active = True)
    session_id = str( (await sessions.insert_one(session.model_dump(exclude = { "id" }))).inserted_id )

    return { "session_id": session_id }

@router.post('/logout', status_code = 200)
async def logout(session: Annotated[Session | None, Depends(retrieve_session)]):    
    if session == None:
        return

    await sessions.update_one({'_id': session.id}, {'$set': {'active': False}})
    