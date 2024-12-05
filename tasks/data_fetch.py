import aiohttp
from datetime import datetime, timezone
import logging
import html
from db.db_utils import get_collection
from typing import Any, List

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Fetch cryptocurrency prices


async def fetch_prices():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "bitcoin,ethereum,cardano", "vs_currencies": "usd"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched price data: {data}")
                    await save_prices_to_db(data)
                else:
                    logger.error(
                        f"Failed to fetch prices. Status: {response.status}")
    except Exception as e:
        logger.exception("Error in fetch_prices")

# Save cryptocurrency prices to the database


async def save_prices_to_db(data: Any) -> None:
    try:
        if not data:
            logger.error("No data provided for saving prices.")
            return

        collection = await get_collection("prices")
        result = await collection.insert_one({
            "data": data,
            "timestamp": datetime.now(timezone.utc)
        })
        logger.info(f"Prices saved successfully with id: {result.inserted_id}")
    except Exception as e:
        logger.exception("Failed to save prices to DB")

# Fetch social trends data from Reddit and store it in MongoDB


async def fetch_and_store_social_data():
    try:
        url = "https://api.reddit.com/r/cryptocurrency/top"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched Reddit data: {data}")
                    children = data.get("data", {}).get("children", [])
                    if isinstance(children, list):
                        collection = await get_collection("social_trends")
                        for item in children:
                            item_data = item.get("data", {})
                            if item_data:
                                item_data["fetched_at"] = datetime.now(
                                    timezone.utc)
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
        logger.exception("Error fetching or storing social data")

# Fetch and store investor data


async def fetch_investors():
    try:
        url = "https://api.some-crypto-investor-api.com/investors"
        params = {"crypto": "bitcoin,ethereum,cardano"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched investor data: {data}")
                    await store_investor_data(data)
                else:
                    logger.error(
                        f"Failed to fetch investor data. Status: {response.status}")
    except Exception as e:
        logger.exception("Error in fetch_investors")

# Store investor data in MongoDB


async def store_investor_data(data: dict):
    try:
        if not data:
            logger.error("No investor data provided.")
            return

        collection = await get_collection("investors")
        for investor in data.get('investors', []):
            await collection.update_one(
                {"name": investor["name"]},
                {"$set": investor},
                upsert=True
            )
        logger.info("Investor data stored successfully.")
    except Exception as e:
        logger.exception("Failed to store investor data")

# Filter cryptocurrencies based on parameters


async def filter_currencies_based_on_params() -> List[dict]:
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {"vs_currency": "usd", "price_change_percentage": "24h"}
        min_price, max_price = 0.1, 10
        min_market_cap, min_volume = 100_000_000, 50_000

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    filtered_coins = [
                        coin for coin in data if min_price <= coin["current_price"] <= max_price and
                        coin["market_cap"] >= min_market_cap and coin["total_volume"] >= min_volume
                    ]
                    logger.info(f"Filtered coins: {filtered_coins}")
                    return filtered_coins
                else:
                    logger.error(
                        f"Failed to fetch currencies. Status: {response.status}")
    except Exception as e:
        logger.exception("Error in filter_currencies_based_on_params")
    return []

# Store filtered cryptocurrencies in MongoDB


async def store_filtered_currencies(currencies: List[dict]):
    try:
        if not currencies:
            logger.warning("No filtered currencies provided.")
            return

        collection = await get_collection("filtered_currencies")
        for currency in currencies:
            await collection.update_one(
                {"id": currency["id"]},
                {"$set": currency},
                upsert=True
            )
        logger.info("Filtered currencies stored successfully.")
    except Exception as e:
        logger.exception("Failed to store filtered currencies")
