import aiohttp
from datetime import datetime
import logging
import html
from db.db_utils import get_collection
from typing import Any


# Change to DEBUG for more verbose logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Function to fetch cryptocurrency prices


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
        logger.error(f"Error in fetch_prices: {e}")

# Function to save cryptocurrency prices to the database


async def save_prices_to_db(data: Any) -> None:
    """
    Save cryptocurrency prices to the MongoDB database.
    """
    try:
        # Ensure 'data' is passed correctly
        if not data:
            logger.error("No data provided for saving prices.")
            return

        # Fetch the collection from the database
        collection = await get_collection("prices")

        # Insert data into the collection
        result = await collection.insert_one({
            "data": data,
            "timestamp": datetime.utcnow()
        })

        # Log the success
        logger.info(f"Prices saved successfully with id: {result.inserted_id}")
    except Exception as e:
        logger.error(f"Failed to save prices to DB: {e}")

# Function to fetch social trends data from Reddit and store it in MongoDB


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
                    logger.info(f"Reddit response fetched: {data}")
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
                                # Log update before performing
                                logger.info(
                                    f"Updating social_trends with ID: {item_data.get('id')}")
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

# Function to fetch investor data from an API and store it in MongoDB


async def fetch_investors():
    """
    Fetchs data about cryptocurrency investors or institutional backers.
    """
    try:
        # Placeholder API for fetching investor data
        url = "https://api.some-crypto-investor-api.com/investors"
        # You can modify this to include other cryptos or params
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
        logger.error(f"Error in fetch_investors: {e}")

# Function to store investor data in MongoDB


async def store_investor_data(data):
    """
    Save investor data to MongoDB.
    """
    try:
        collection = await get_collection("investors")
        for investor in data.get('investors', []):
            # Log before inserting
            logger.info(f"Inserting/updating investor: {investor['name']}")
            await collection.update_one(
                {"name": investor["name"]},  # Assuming 'name' is unique
                {"$set": investor},
                upsert=True
            )
        logger.info("Investor data stored successfully.")
    except Exception as e:
        logger.error(f"Failed to store investor data: {e}")

# Function to filter cryptocurrencies based on price, market cap, and volume


async def filter_currencies_based_on_params():
    """
    Filters cryptocurrencies based on parameters like price range, market cap, and volume.
    """
    try:
        # Example filtering parameters (can be modified or taken from a config)
        min_price = 0.1
        max_price = 10
        min_market_cap = 100_000_000  # USD
        min_volume = 50_000  # USD

        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {"vs_currency": "usd", "price_change_percentage": "24h"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    filtered_coins = [
                        coin for coin in data if min_price <= coin["current_price"] <= max_price and
                        coin["market_cap"] >= min_market_cap and coin["total_volume"] >= min_volume
                    ]
                    logger.info(f"Filtered coins: {filtered_coins}")
                    await store_filtered_currencies(filtered_coins)
                else:
                    logger.error(
                        f"Failed to fetch currencies. Status: {response.status}")
    except Exception as e:
        logger.error(f"Error in filter_currencies_based_on_params: {e}")

# Function to store filtered cryptocurrencies in MongoDB


async def store_filtered_currencies(currencies):
    """
    Save filtered currencies to MongoDB.
    """
    try:
        collection = await get_collection("filtered_currencies")
        for currency in currencies:
            logger.info(
                f"Inserting/updating filtered currency: {currency['id']}")
            await collection.update_one(
                {"id": currency["id"]},
                {"$set": currency},
                upsert=True
            )
        logger.info("Filtered currencies stored successfully.")
    except Exception as e:
        logger.error(f"Failed to store filtered currencies: {e}")
