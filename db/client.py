from dotenv import load_dotenv
import os

from motor import motor_asyncio

load_dotenv()
mongodb_uri = os.environ["MONGODB_URI"]

client = motor_asyncio.AsyncIOMotorClient(mongodb_uri)
database = client["Original"]

users = database["users"]
user_access = database["user_access"]
transactions = database["transactions"]
admins = database["admins"]
subaccounts = database["subaccounts"]
sessions = database["sessions"]
deposits = database["deposits"]
