from datetime import datetime, timezone
import asyncio
from db.database import get_database  # Import your get_database function


async def insert_sample_prices():
    # Get the database (no need to await here)
    db = get_database()  # Ensure this returns the database object for 'auth_roles'
    prices_collection = db["prices"]  # Access the 'prices' collection

    # Define sample data with a UTC-aware timestamp
    sample_data = [
        {"symbol": "bitcoin", "price": 48000,
            "timestamp": datetime.now(timezone.utc)},
        {"symbol": "ethereum", "price": 1800,
            "timestamp": datetime.now(timezone.utc)},
        {"symbol": "cardano", "price": 0.35,
            "timestamp": datetime.now(timezone.utc)},
    ]

    # Insert the sample data into the collection
    await prices_collection.insert_many(sample_data)
    print("Sample prices inserted successfully into 'auth_roles' database!")


# Run the script
if __name__ == "__main__":
    asyncio.run(insert_sample_prices())
