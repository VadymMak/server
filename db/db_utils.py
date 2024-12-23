from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
import certifi
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


async def get_database() -> AsyncIOMotorDatabase:
    """
    Returns an AsyncIOMotorDatabase to interact with the MongoDB database.
    """
    mongo_uri = os.getenv("MONGO_URI")

    if not mongo_uri:
        raise ValueError("MongoDB URI is not set in the environment variables")

    print(f"Connecting to MongoDB at {mongo_uri}")

    # Initialize the MongoDB client with tlsCAFile pointing to the certifi CA file
    client = AsyncIOMotorClient(
        mongo_uri,
        tls=True,  # Enable TLS/SSL
        tlsCAFile=certifi.where()  # Use certifi's CA certificates
    )

    # Replace with the actual database name you are using
    db = client["auth_roles"]  # Specify the database name here
    return db


async def get_collection(collection_name: str) -> AsyncIOMotorCollection:
    """
    Returns a specific collection from the MongoDB database.
    """
    db = await get_database()  # Await the database connection
    # Directly access the collection from the database
    collection = db[collection_name]
    return collection
