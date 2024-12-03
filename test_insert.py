import asyncio
from db.database import get_database


async def insert_and_check_data():
    """
    Insert sample data into the MongoDB 'social_trends' collection and check the data.
    """
    try:
        # Get the database instance
        db = await get_database()

        # Define the sample data to insert
        sample_data = {
            "symbol": "ETH",
            "trend_score": 73,
            "trend_description": "Ethereum is gaining momentum."
        }

        # Insert data into the 'social_trends' collection
        result = await db["social_trends"].insert_one(sample_data)
        print(f"Inserted document with ID: {result.inserted_id}")

        # Retrieve the latest data from the 'social_trends' collection
        latest_data = await db["social_trends"].find_one(
            {}, sort=[("_id", -1)]
        )
        print("Latest data in 'social_trends' collection:")
        print(latest_data)

    except Exception as e:
        print(f"Error: {e}")


# Run the test
if __name__ == "__main__":
    asyncio.run(insert_and_check_data())
