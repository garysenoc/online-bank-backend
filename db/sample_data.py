from datetime import datetime, timedelta
from pymongo import MongoClient
from bson import ObjectId
import random
import names

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['original']  # Replace with your actual database name

def generate_account_number():
    return ''.join([str(random.randint(0, 9)) for _ in range(10)])

def generate_routing_number():
    return ''.join([str(random.randint(0, 9)) for _ in range(9)])

def clear_collections():
    """Clear all collections before inserting sample data"""
    collections = ['users', 'subaccounts', 'transactions', 'payments']
    for collection in collections:
        db[collection].delete_many({})

def create_sample_users():
    """Generate sample users"""
    users = []
    for _ in range(5):
        user = {
            "_id": ObjectId(),
            "name": names.get_full_name(),
            "blocked": False,
            "configuration": {
                "card_deposit": random.choice([True, False])
            }
        }
        users.append(user)
    db.users.insert_many(users)
    return users

def create_sample_subaccounts(users):
    """Generate sample subaccounts for users"""
    subaccounts = []
    for user in users:
        # Create 1-3 subaccounts per user
        for _ in range(random.randint(1, 3)):
            subaccount = {
                "_id": ObjectId(),
                "admin_id": user["_id"],
                "owner_id": user["_id"],
                "name": f"Account {random.randint(1, 999)}",
                "routing_number": generate_routing_number(),
                "account_number": generate_account_number(),
                "balance": {
                    "total": random.randint(1000, 100000),
                    "processing": random.randint(0, 1000)
                }
            }
            subaccounts.append(subaccount)
    db.subaccounts.insert_many(subaccounts)
    return subaccounts

def create_sample_transactions(subaccounts):
    """Generate sample transactions between subaccounts"""
    transactions = []
    statuses = ["pending", "processing", "completed", "cancelled", "failed"]
    priorities = ["low", "medium", "high"]
    
    for _ in range(20):
        sender = random.choice(subaccounts)
        recipient = random.choice(subaccounts)
        while recipient["_id"] == sender["_id"]:
            recipient = random.choice(subaccounts)
            
        amount = random.randint(10, 1000)
        status = random.choice(statuses)
        requested_date = datetime.now() - timedelta(days=random.randint(0, 30))
        
        transaction = {
            "_id": ObjectId(),
            "sender": str(sender["_id"]),
            "recipient": {
                "fullname": names.get_full_name(),
                "account_number": recipient["account_number"],
                "routing_number": recipient["routing_number"]
            },
            "amount": float(amount),
            "fee": {
                "base": float(amount * 0.01),
                "priority": float(amount * 0.005)
            },
            "priority": random.choice(priorities),
            "date": {
                "requested": requested_date,
                "concluded": requested_date + timedelta(days=1) if status in ["completed", "failed", "cancelled"] else None
            },
            "notes": [f"Sample transaction note {i+1}" for i in range(random.randint(0, 2))],
            "status": status
        }
        transactions.append(transaction)
    db.transactions.insert_many(transactions)

def create_sample_deposits(subaccounts):
    """Generate sample deposits"""
    deposits = []
    for _ in range(10):
        recipient = random.choice(subaccounts)
        deposit = {
            "_id": ObjectId(),
            "recipient": str(recipient["_id"]),
            "amount": float(random.randint(100, 5000)),
            "status": random.choice(["pending", "completed"]),
            "type": random.choice(["card", "bank"]),
            "date": datetime.now() - timedelta(days=random.randint(0, 15))
        }
        deposits.append(deposit)
    db.deposits.insert_many(deposits)

def generate_sample_data():
    """Main function to generate all sample data"""
    print("Clearing existing data...")
    clear_collections()
    
    print("Generating sample users...")
    users = create_sample_users()
    
    print("Generating sample subaccounts...")
    subaccounts = create_sample_subaccounts(users)
    
    print("Generating sample transactions...")
    create_sample_transactions(subaccounts)
    
    print("Generating sample deposits...")
    create_sample_deposits(subaccounts)
    
    print("Sample data generation completed!")

if __name__ == "__main__":
    generate_sample_data() 