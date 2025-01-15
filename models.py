import requests
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

load_dotenv()

async def save_analysis_in_mongo(collection, paper):
    # Initialize MongoDB connection
    mongodb_client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    mongodb = mongodb_client[os.getenv("MONGODB_DB_NAME")]
    collection = mongodb[collection]

        # Save to MongoDB
    await collection.insert_one(paper)

    mongodb_client.close()
    return 1

