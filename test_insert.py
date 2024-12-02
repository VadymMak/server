import asyncio
from db.database import get_database


async def insert_sample_data():
    db = get_database()
    sample_data = {
        "symbol": "ETH",
        "trend_score": 95,
        "trend_description": "Ethereum is gaining momentum."
    }
    try:
        result = await db.social_trends.insert_one(sample_data)
        print(f"Inserted document with ID: {result.inserted_id}")
    except Exception as e:
        print("Error inserting data:", e)

# Run the test
if __name__ == "__main__":
    asyncio.run(insert_sample_data())
