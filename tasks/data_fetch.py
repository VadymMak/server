import aiohttp
from datetime import datetime, timezone
import logging
import os
import html
from db.db_utils import get_collection
from typing import Any, List
from dotenv import load_dotenv

from models.social_model import SocialModel

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Reddit credentials from environment variables
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT')

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
        # Get access token from Reddit using client credentials
        auth = aiohttp.BasicAuth(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
        token_url = "https://www.reddit.com/api/v1/access_token"
        headers = {'User-Agent': REDDIT_USER_AGENT}

        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data={'grant_type': 'client_credentials'},
                                    auth=auth, headers=headers) as response:
                if response.status == 200:
                    token_data = await response.json()
                    access_token = token_data.get('access_token')

                    if not access_token:
                        logger.error("No access token received.")
                        return

                    logger.info("Successfully retrieved access token.")
                    # Fetch top posts from /r/cryptocurrency
                    reddit_url = "https://oauth.reddit.com/r/cryptocurrency/top"
                    headers['Authorization'] = f"bearer {access_token}"

                    async with session.get(reddit_url, headers=headers) as reddit_response:
                        if reddit_response.status == 200:
                            data = await reddit_response.json()
                            logger.info(f"Reddit response fetched: {data}")

                            # Extract posts data
                            children = data.get("data", {}).get("children", [])

                            if not isinstance(children, list):
                                logger.warning(
                                    "Invalid 'children' format in response.")
                                return

                            collection = await get_collection("social_trends")

                            for item in children:
                                post_data = item.get("data", {})

                                # Ensure required fields are present
                                if "id" not in post_data:
                                    logger.warning(
                                        f"Post missing 'id': {post_data}")
                                    continue

                                # Map Reddit data to SocialModel fields
                                social_entry = {
                                    # Or another logic for symbol
                                    "symbol": post_data.get("title", "Unknown"),
                                    "platform": "Reddit",  # Platform is hardcoded here, you could add more logic if needed
                                    # Using comments as a proxy for followers
                                    "followers": post_data.get("num_comments", 0),
                                    # Calculate engagement as an example
                                    "engagement": post_data.get("ups", 0) / max(post_data.get("num_comments", 1), 1),
                                    "timestamp": datetime.now(),  # Use current timestamp
                                    "trend": "Neutral",  # Default trend
                                    # Using comments as mentions
                                    "mentions": post_data.get("num_comments", 0),
                                    "positive_sentiment": 0.5,  # Default sentiment
                                    "date": datetime.now(),  # Use current timestamp as date
                                }

                                # Create SocialModel instance and validate
                                try:
                                    social_entry_model = SocialModel(
                                        **social_entry)
                                except ValueError as e:
                                    logger.error(
                                        f"Error validating social entry: {e}")
                                    continue

                                # Insert or update in MongoDB
                                result = await collection.update_one(
                                    {"id": post_data["id"]},
                                    {"$set": social_entry_model.dict()},
                                    upsert=True
                                )

                                if result.modified_count == 0:
                                    logger.warning(
                                        f"Social entry with id {post_data['id']} was not updated.")
                                else:
                                    logger.info(
                                        f"Social entry with id {post_data['id']} was updated.")

                            logger.info(
                                "Social trends data stored successfully.")
                        else:
                            logger.error(
                                f"Failed to fetch social data. Status: {reddit_response.status}")
                else:
                    logger.error(
                        f"Failed to authenticate. Status: {response.status}")
    except Exception as e:
        logger.error(f"Error fetching or storing social data: {e}")


# Fetch and store investor data

async def fetch_investors():
    try:
        # Placeholder API URL
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
        logger.error(f"Error in fetch_investors: {e}")

# Store investor data to MongoDB


async def store_investor_data(data):
    try:
        investors = data.get("investors", [])

        if not isinstance(investors, list):
            logger.warning("Investors data is not a list.")
            return

        collection = await get_collection("investors")

        for investor in investors:
            if "name" not in investor:
                logger.warning(f"Missing 'name' field in investor: {investor}")
                continue

            investor_entry = {
                "name": investor["name"],
                "cryptos_supported": investor.get("cryptos_supported", []),
                "amount_invested": investor.get("amount_invested", "unknown"),
                "fetched_at": datetime.now(timezone.utc),
            }

            await collection.update_one(
                {"name": investor_entry["name"]},
                {"$set": investor_entry},
                upsert=True
            )

        logger.info("Investor data stored successfully.")
    except Exception as e:
        logger.error(f"Failed to store investor data: {e}")

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
