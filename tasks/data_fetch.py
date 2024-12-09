import aiohttp
from datetime import datetime, timezone
import logging
import os
from db.db_utils import get_collection
from pymongo.collection import Collection
from typing import Any, List, Dict
from dotenv import load_dotenv
from models.social_model import SocialModel

load_dotenv()

# Configure logging with timestamp
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Reddit credentials from environment variables
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT')

# Default filter values
DEFAULT_MIN_PRICE = 0
DEFAULT_MAX_PRICE = 1  # Set default maximum price to 1
MIN_MARKET_CAP = 100_000_000
MIN_VOLUME = 50_000

# Function to fetch cryptocurrency prices from CoinGecko API


async def fetch_prices(min_price: float = DEFAULT_MIN_PRICE, max_price: float = DEFAULT_MAX_PRICE):
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,ethereum,cardano",  # You can add more coins here
            "vs_currencies": "usd",
            "include_market_cap": "true",
            "include_24hr_vol": "true"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched price data: {data}")

                    # Filter data based on conditions
                    filtered_data = filter_prices(data, min_price, max_price)
                    if filtered_data:
                        # Log filtered data
                        logger.info(f"Filtered data: {filtered_data}")
                        # Store the filtered prices
                        await store_prices_to_db(filtered_data)
                    else:
                        logger.info(
                            "No data after filtering based on conditions.")
                else:
                    logger.error(
                        f"Failed to fetch prices. Status: {response.status}")
    except Exception as e:
        logger.exception("Error in fetch_prices")

# Function to filter fetched prices based on market cap, volume, and price range


def filter_prices(data: Dict, min_price: float, max_price: float) -> Dict:
    filtered = {}
    for coin_id, coin_data in data.items():
        if (min_price <= coin_data["usd"] <= max_price and
            coin_data.get("usd_market_cap", 0) >= MIN_MARKET_CAP and
                coin_data.get("usd_24h_vol", 0) >= MIN_VOLUME):
            filtered[coin_id] = coin_data
    return filtered

# Function to store prices to MongoDB


async def store_prices_to_db(data: Any) -> None:
    try:
        if not data:
            logger.error("No data provided for saving prices.")
            return

        # Ensure data is in the expected format
        logger.info(f"Data to save: {data}")

        # Get MongoDB collection
        collection = await get_collection("prices")

        # Log the collection to ensure it's valid
        if not collection:
            logger.error("Collection 'prices' not found.")
            return

        # Prepare the data for insertion
        insert_data = {
            "data": data,
            "timestamp": datetime.now(timezone.utc)
        }

        # Insert the data into MongoDB
        result = await collection.insert_one(insert_data)

        logger.info(f"Prices saved successfully with id: {result.inserted_id}")
    except Exception as e:
        logger.exception("Failed to save prices to DB")

# Fetch and store social data from Reddit


async def fetch_and_store_social_data():
    try:
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
                                    "symbol": post_data.get("title", "Unknown"),
                                    "platform": "Reddit",
                                    "followers": post_data.get("num_comments", 0),
                                    "engagement": post_data.get("ups", 0) / max(post_data.get("num_comments", 1), 1),
                                    "timestamp": datetime.now(),
                                    "trend": "Neutral",
                                    "mentions": post_data.get("num_comments", 0),
                                    "positive_sentiment": 0.5,
                                    "date": datetime.now(),
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

# Placeholder MongoDB collection fetch function


async def get_collection(collection_name: str):
    # Connect to MongoDB and return collection object
    pass
