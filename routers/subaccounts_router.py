from fastapi import APIRouter, HTTPException, Depends
from pyobjectID import PyObjectId, MongoObjectId
from pymongo import ReturnDocument
from typing import Annotated
from bson import ObjectId

from db.client import subaccounts
from db.models.subaccount import Subaccount, CreateSubaccount, Balance
from dependencies.session import validate_session

router = APIRouter(
    prefix="/subaccounts"
)

async def get_subaccounts_array_id(session: dict) -> list[str]:
    subaccount_filter_criteria = { "admin_id": session["id"] } if session["role"] == "admin" else { "owner_id": session["id"] }
    subaccounts_ids_raw = await subaccounts.find(subaccount_filter_criteria).to_list()
    subaccounts_ids = [ str(subaccount["_id"]) for subaccount in subaccounts_ids_raw ]

    return subaccounts_ids

async def get_subaccounts_msb(session: dict) -> list[Subaccount]:
    subaccounts_raw = await subaccounts.find({ 'owner_id': str(session['id']) }).to_list()
    
    res_subaccounts = []
    for subaccount_raw in subaccounts_raw:
        res_subaccounts.append(Subaccount(**subaccount_raw))
    
    return res_subaccounts

async def get_subaccounts_admin(session: dict) -> list[Subaccount]:
    subaccounts_raw = await subaccounts.find({ 'admin_id': str(session['id']) }).to_list()
    
    res_subaccounts = []
    for subaccount_raw in subaccounts_raw:
        res_subaccounts.append(Subaccount(**subaccount_raw))
    
    return res_subaccounts

@router.get("/")
async def get_subaccounts(session: Annotated[dict, Depends(validate_session)]):
    if session['role'] == 'msb':
        return await get_subaccounts_msb(session)
    elif session['role'] == 'admin':
        return await get_subaccounts_admin(session)
    
    return [] # for lint

async def get_subaccount_by_id(subaccount_id: str, requester_id: str):
    subaccount_found = await subaccounts.find_one({
        "_id": PyObjectId.to_object(subaccount_id)
    })

    if subaccount_found is None:
        raise HTTPException(status_code=404, detail="Subaccount was not found")
    
    subaccount = Subaccount(**subaccount_found)

    if str(requester_id) != str(subaccount.admin_id) and str(requester_id) != str(subaccount.owner_id):
        raise HTTPException(status_code=404, detail="You don't have permission to view this subaccount")
    
    return subaccount

@router.get("/{subaccount_id}")
async def get_subaccounts(subaccount_id: str, session: Annotated[dict, Depends(validate_session)]):
    return await get_subaccount_by_id(subaccount_id, session["id"])

@router.post("/")
async def create_subaccount(subaccount_payload: CreateSubaccount):
    subaccount_instance = Subaccount(**subaccount_payload.model_dump())
    created_subaccount_id = (await subaccounts.insert_one(subaccount_instance.model_dump(exclude={"_id"}))).inserted_id
    return { 'subaccount': str(created_subaccount_id) }

@router.post("/{subaccount_id}/balance")
async def update_subaccount_balance(subaccount_id: str, balance: Balance, session: Annotated[dict, Depends(validate_session)]):
    subaccount = await get_subaccount_by_id(subaccount_id, session["id"])

    if str(subaccount.admin_id) != str(session["id"]):
        raise HTTPException(status_code=404, detail="You don't have permission to edit this subaccount")
    
    subaccount.balance = balance
    await subaccounts.update_one({'_id': ObjectId(subaccount.id)}, {'$set': subaccount.model_dump(by_alias = True, exclude = {"id"})})
    
    return {}

#@router.delete("/subaccount/{subaccount_id}")
#def delete_subaccount(user_id:str, subaccount_id:str):
    deleted_subaccount = users_subaccount.find_one_and_delete({
        "_id": PyObjectId.to_object(subaccount_id),
    })
    
    if deleted_subaccount is None:
        raise HTTPException(status_code=404, detail="Subaccount was not found")
    
    return UsersSubaccount(**deleted_subaccount)


#@router.put("/subaccount/{subaccount_id}")
#def edit_subaccount(user_id:str, subaccount_id:str, newSubaccountInfo:EditSubaccount):
    subaccountInfoToUpdate = {}
    
    if newSubaccountInfo.subaccountName != "":
        subaccountInfoToUpdate["subaccountName"] = newSubaccountInfo.subaccountName
    if newSubaccountInfo.routingNumber != -1:
        subaccountInfoToUpdate["routingNumber"] = newSubaccountInfo.routingNumber
    if newSubaccountInfo.subaccountType != "":
        subaccountInfoToUpdate["subaccountType"] = newSubaccountInfo.subaccountType
    if newSubaccountInfo.clientName != "":
        subaccountInfoToUpdate["clientName"] = newSubaccountInfo.clientName
    if newSubaccountInfo.contactInfo != "":
        subaccountInfoToUpdate["contactInfo"] = newSubaccountInfo.contactInfo

    updated_subaccount = users_subaccount.find_one_and_update(
        {
            "_id": PyObjectId.to_object(subaccount_id),
            "parentAccountID": user_id,
        },
        {"$set": subaccountInfoToUpdate},
        return_document=ReturnDocument.AFTER
    )

    if updated_subaccount is None:
        raise HTTPException(status_code=404, detail="user or subaccount was not found")

    return UsersSubaccount(**updated_subaccount)

    