import asyncio
from db.database import get_database


async def fetch_data():
    db = get_database()
    try:
        # Fetch all documents in the social_trends collection
        cursor = db.social_trends.find()
        documents = await cursor.to_list(length=100)
        print("Fetched documents:")
        for doc in documents:
            print(doc)
    except Exception as e:
        print("Error fetching data:", e)

# Run the test
if __name__ == "__main__":
    asyncio.run(fetch_data())
