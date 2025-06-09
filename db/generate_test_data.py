from motor import motor_asyncio
import asyncio
from bson import ObjectId
from passlib.hash import bcrypt
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import random

# Load environment variables
load_dotenv()
mongodb_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")

async def clear_collections(db):
    """Clear all existing data"""
    collections = ['users', 'user_access', 'admins', 'subaccounts', 'transactions', 'deposits', 'sessions']
    for collection in collections:
        await db[collection].delete_many({})

async def create_test_users(db):
    """Create test MSB users"""
    users = []
    user_credentials = []
    
    # Create 3 MSB users
    for i in range(3):
        user_id = ObjectId()
        user = {
            "_id": user_id,
            "name": f"MSB User {i+1}",
            "blocked": False,
            "configuration": {
                "card_deposit": bool(i % 2)  # Alternate between True and False
            }
        }
        
        user_access = {
            "email": f"msb{i+1}@example.com",
            "role": "msb",
            "hashed_password": bcrypt.hash(str(user_id) + "password123"),
            "user_id": str(user_id)
        }
        
        users.append(user)
        user_credentials.append(user_access)
        print(f"Created MSB User {i+1}:")
        print(f"Email: msb{i+1}@example.com")
        print(f"Password: password123")
        print("---")
    
    await db["users"].insert_many(users)
    await db["user_access"].insert_many(user_credentials)
    return users

async def create_test_subaccounts(db, users):
    """Create test subaccounts for users"""
    subaccounts = []
    
    for user in users:
        # Create 2 subaccounts per user
        for i in range(2):
            subaccount = {
                "_id": ObjectId(),
                "admin_id": str(user["_id"]),
                "owner_id": str(user["_id"]),
                "name": f"Account {i+1} - {user['name']}",
                "routing_number": ''.join([str(random.randint(0, 9)) for _ in range(9)]),
                "account_number": ''.join([str(random.randint(0, 9)) for _ in range(10)]),
                "balance": {
                    "total": random.randint(1000, 10000),
                    "processing": 0
                }
            }
            subaccounts.append(subaccount)
    
    await db["subaccounts"].insert_many(subaccounts)
    return subaccounts

async def create_test_transactions(db, subaccounts):
    """Create test transactions between subaccounts"""
    transactions = []
    statuses = ["pending", "processing", "completed"]
    priorities = ["low", "medium", "high"]
    
    # Create 10 transactions
    for _ in range(10):
        sender = random.choice(subaccounts)
        recipient = random.choice(subaccounts)
        while recipient["_id"] == sender["_id"]:
            recipient = random.choice(subaccounts)
        
        amount = random.randint(100, 1000)
        status = random.choice(statuses)
        priority = random.choice(priorities)
        
        base_fee = round(amount * 0.01, 2)  # 1% base fee
        priority_fee = round(amount * (0.005 if priority == "high" else 0.002), 2)
        
        requested_date = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 5))
        concluded_date = requested_date + timedelta(hours=random.randint(1, 24)) if status == "completed" else None
        
        transaction = {
            "_id": ObjectId(),
            "sender_subaccount": str(sender["_id"]),
            "recipient": {
                "fullname": f"Recipient for {recipient['name']}",
                "account_number": recipient["account_number"],
                "routing_number": recipient["routing_number"]
            },
            "amount": float(amount),
            "fee": {
                "base": base_fee,
                "priority": priority_fee
            },
            "priority": priority,
            "date": {
                "requested": requested_date,
                "concluded": concluded_date
            },
            "notes": [f"Test transaction note {random.randint(1, 100)}"],
            "status": status
        }
        transactions.append(transaction)
    
    await db["transactions"].insert_many(transactions)

async def create_test_deposits(db, subaccounts):
    """Create test deposits"""
    deposits = []
    
    # Create 5 deposits
    for _ in range(5):
        recipient = random.choice(subaccounts)
        amount = random.randint(500, 2000)
        
        deposit = {
            "_id": ObjectId(),
            "recipient_subaccount": str(recipient["_id"]),
            "deposit_amount": float(amount),
            "status": "completed",
            "type": random.choice(["card", "bank"]),
            "date": datetime.now(timezone.utc) - timedelta(days=random.randint(0, 10)),
            "source": {
                "type": "card",
                "last4": str(random.randint(1000, 9999)),
                "expiry_month": random.randint(1, 12),
                "expiry_year": random.randint(2024, 2028)
            }
        }
        deposits.append(deposit)
    
    await db["deposits"].insert_many(deposits)

async def generate_test_data():
    """Main function to generate all test data"""
    # Connect to MongoDB
    client = motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    db = client["Original"]
    
    print("Clearing existing data...")
    await clear_collections(db)
    
    print("\nCreating test users...")
    users = await create_test_users(db)
    
    print("\nCreating test subaccounts...")
    subaccounts = await create_test_subaccounts(db, users)
    
    print("\nCreating test transactions...")
    await create_test_transactions(db, subaccounts)
    
    print("\nCreating test deposits...")
    await create_test_deposits(db, subaccounts)
    
    print("\nTest data generation completed!")
    print("\nYou can now log in with any of the following credentials:")
    print("Admin credentials:")
    print("Email: admin@example.com")
    print("Password: admin123")
    print("\nMSB User credentials:")
    for i in range(3):
        print(f"MSB User {i+1}:")
        print(f"Email: msb{i+1}@example.com")
        print(f"Password: password123")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(generate_test_data()) 