from motor import motor_asyncio
import asyncio
from bson import ObjectId
from passlib.hash import bcrypt
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
mongodb_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")

async def create_admin_user():
    # Connect to MongoDB
    client = motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    db = client["Original"]
    
    # Create admin user
    admin_id = ObjectId()
    admin_data = {
        "_id": admin_id,
        "name": "Admin User"
    }
    
    # Create admin credentials
    admin_access = {
        "email": "admin@example.com",
        "role": "admin",
        "hashed_password": bcrypt.hash(str(admin_id) + "admin123"),
        "user_id": str(admin_id)
    }
    
    # Insert admin user and credentials
    await db["admins"].insert_one(admin_data)
    await db["user_access"].insert_one(admin_access)
    
    print("Admin user created successfully!")
    print("Login credentials:")
    print("Email: admin@example.com")
    print("Password: admin123")

if __name__ == "__main__":
    asyncio.run(create_admin_user()) 