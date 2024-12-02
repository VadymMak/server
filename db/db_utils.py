from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
import certifi
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_database() -> AsyncIOMotorDatabase:
    """
    Returns an AsyncIOMotorDatabase to interact with the MongoDB database.
    """
    mongo_uri = os.getenv("MONGO_URI")

    if not mongo_uri:
        raise ValueError("MongoDB URI is not set in the environment variables")

    # Initialize the MongoDB client with tlsCAFile pointing to the certifi CA file
    client = AsyncIOMotorClient(
        mongo_uri,
        tls=True,  # Enable TLS/SSL
        tlsCAFile=certifi.where()  # Use certifi's CA certificates
    )

    # Replace with the actual database name you are using
    db = client["auth_roles"]  # Specify the database name here
    return db


def get_collection(collection_name: str) -> AsyncIOMotorCollection:
    """
    Returns a specific collection from the MongoDB database.
    """
    db = get_database()  # Get the database
    return db[collection_name]  # Access the specified collection
