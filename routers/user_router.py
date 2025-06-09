from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from pyobjectID import MongoObjectId
from passlib.hash import bcrypt
from typing import Annotated

from db.client import users, user_access
from db.models.users import User
from db.models.user_access import CreateUserAccess, UserAccess
from dependencies.session import validate_session

router = APIRouter(
    prefix="/user",
    tags=["users"],
    responses={
        404: {"description": "User not found"},
        403: {"description": "Permission denied"},
    }
)

@router.get("/", 
    response_model=User | list[User],
    status_code=200,
    summary="Get user(s) information",
    description="""
    Retrieve user information. If a user_id is provided, returns a single user.
    If no user_id is provided, returns all users. Requires admin privileges.
    """
)
async def get_users(
    session: Annotated[dict, Depends(validate_session)], 
    user_id: str = ""
) -> User | list[User]:
    """
    Get user information.

    Args:
        session: Validated session information
        user_id: Optional user ID to get specific user

    Returns:
        User or list[User]: Single user or list of all users

    Raises:
        HTTPException: 403 if user is not admin
        HTTPException: 404 if specific user is not found
    """
    if session["role"] != "admin":
        raise HTTPException(status_code=403, detail="This user has not the right permissions")
    
    if user_id != "":
        user = await users.find_one({"_id": ObjectId(user_id)})
        if user == None:
            raise HTTPException(status_code=404, detail="User not found")
        return User(**user)

    users_cursor = users.find()
    return [User(**user) for user in await users_cursor.to_list()]

@router.post("/", 
    response_model=User,
    status_code=201,
    summary="Create a new user",
    description="""
    Create a new user with the provided information.
    Requires admin privileges. Creates both user profile and access credentials.
    """
)
async def create_user(
    payload: CreateUserAccess, 
    session: Annotated[dict, Depends(validate_session)]
) -> User:
    """
    Create a new user.

    Args:
        payload: User creation data including name, email, and password
        session: Validated session information

    Returns:
        User: Created user information

    Raises:
        HTTPException: 403 if user is not admin
    """
    if session["role"] != "admin":
        raise HTTPException(status_code=403, detail="This user has not the right permissions")
    
    new_user = User(name=payload.name)
    inserted_user = await users.insert_one(new_user.model_dump(by_alias=True, exclude={"id"}))

    new_user_access = UserAccess(
        email=payload.email,
        hashed_password=bcrypt.hash(MongoObjectId.to_string(inserted_user.inserted_id) + payload.password),
        role="msb",
        user_id=MongoObjectId.to_string(inserted_user.inserted_id)
    )

    new_user_access.id = (await user_access.insert_one(new_user_access.model_dump(by_alias=True, exclude={"id"}))).inserted_id

    return new_user