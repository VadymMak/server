import certifi
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables from .env file
load_dotenv()

# Print where certifi's CA certificates are located (for debugging purposes)
print("Certifi CA file location:", certifi.where())


async def get_database():
    """
    Returns an AsyncIOMotorClient to interact with the MongoDB database.
    """
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MongoDB URI is not set in the environment variables")

    # Initialize the MongoDB client with TLS/SSL
    client = AsyncIOMotorClient(
        mongo_uri,
        tls=True,  # Enable TLS/SSL
        tlsCAFile=certifi.where()  # Use certifi's CA certificates
    )

    # Specify the actual database name
    db = client["auth_roles"]  # Replace with your actual database name
    return db


async def verify_connection():
    """
    Verifies the connection to MongoDB by attempting to fetch a simple document.
    """
    db = await get_database()  # Await for the database connection asynchronously
    try:
        # Try to fetch a document from the 'social_trends' collection (or any other collection)
        sample_doc = await db.social_trends.find_one()
        if sample_doc is None:
            print("MongoDB connection successful, but no data found.")
        else:
            print("MongoDB connection successful!")
    except Exception as e:
        print("Failed to connect to MongoDB:", e)


# Test the connection by running the verification function
if __name__ == "__main__":
    asyncio.run(verify_connection())  # Run the async verification function
