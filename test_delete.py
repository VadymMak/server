import asyncio
from db.database import get_database


async def delete_sample_data():
    db = get_database()
    try:
        result = await db.social_trends.delete_one({"symbol": "ETH"})
        print(f"Deleted {result.deleted_count} document(s).")
    except Exception as e:
        print("Error deleting data:", e)

if __name__ == "__main__":
    asyncio.run(delete_sample_data())
