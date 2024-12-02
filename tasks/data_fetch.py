import aiohttp
from db.db_utils import get_collection
from datetime import datetime
import logging
import html

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fetch_prices():
    """
    Fetches cryptocurrency prices from the CoinGecko API and stores them in MongoDB.
    """
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "bitcoin,ethereum,cardano", "vs_currencies": "usd"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    await save_prices_to_db(data)
                else:
                    logger.error(
                        f"Failed to fetch prices. Status: {response.status}")
    except Exception as e:
        logger.error(f"Error in fetch_prices: {e}")


async def save_prices_to_db(data):
    """
    Save cryptocurrency prices to the MongoDB database.
    """
    try:
        collection = await get_collection("prices")
        await collection.insert_one({
            "data": data,
            "timestamp": datetime.utcnow()
        })
        logger.info("Prices saved successfully.")
    except Exception as e:
        logger.error(f"Failed to save prices to DB: {e}")


async def fetch_and_store_social_data():
    """
    Fetch social trends data from Reddit and store it in MongoDB.
    """
    try:
        url = "https://api.reddit.com/r/cryptocurrency/top"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Reddit response fetched successfully.")
                    children = data.get("data", {}).get("children", [])
                    if isinstance(children, list):
                        collection = await get_collection("social_trends")
                        for item in children:
                            if "data" in item:
                                item_data = item["data"]
                                item_data["fetched_at"] = datetime.utcnow()
                                if "selftext_html" in item_data:
                                    item_data["selftext_html"] = html.unescape(
                                        item_data["selftext_html"])
                                await collection.update_one(
                                    {"id": item_data.get("id")},
                                    {"$set": item_data},
                                    upsert=True
                                )
                        logger.info(
                            "Social data processed and stored successfully.")
                    else:
                        logger.warning(
                            "No valid 'children' data found in the response.")
                else:
                    logger.error(
                        f"Failed to fetch social data. Status: {response.status}")
    except Exception as e:
        logger.error(f"Error fetching or storing social data: {e}")
