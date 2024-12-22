import aiohttp
from datetime import datetime, timezone
import logging
import os
from db.db_utils import get_collection
from db.database import get_database  # Import the database connection function
from pymongo.collection import Collection
from typing import Any, List, Dict
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

# Default filter values
DEFAULT_MIN_PRICE = 0
DEFAULT_MAX_PRICE = 1  # Set default maximum price to 0.1
MIN_MARKET_CAP = 100_000_000
MIN_VOLUME = 50_000

# Function to fetch prices from CoinGecko


async def fetch_prices(min_price: float = DEFAULT_MIN_PRICE, max_price: float = DEFAULT_MAX_PRICE):
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "bitcoin,ethereum,cardano", "vs_currencies": "usd",
                  "include_market_cap": "true", "include_24hr_vol": "true"}

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
                        await save_prices_to_db(filtered_data)
                    else:
                        logger.info(
                            "No data after filtering based on conditions.")
                else:
                    logger.error(
                        f"Failed to fetch prices. Status: {response.status}")
    except Exception as e:
        logger.exception("Error in fetch_prices")


async def get_collection(collection_name: str):
    try:
        db = await get_database()  # Assuming get_db() is the function that retrieves the DB
        collection = db[collection_name]
        if not collection:
            logger.error(f"Collection '{collection_name}' not found.")
        else:
            logger.info(
                f"Successfully retrieved collection: {collection_name}")
        return collection
    except Exception as e:
        logger.exception(
            f"Error while getting collection '{collection_name}': {e}")
        return None  # Ensure we return None if an error occurs

# Function to filter fetched prices based on market cap, volume, and price range


def filter_prices(data: Dict, min_price: float, max_price: float) -> Dict:
    filtered = {}
    for coin_id, coin_data in data.items():
        if (min_price <= coin_data["usd"] <= max_price and
            coin_data.get("usd_market_cap", 0) >= MIN_MARKET_CAP and
                coin_data.get("usd_24h_vol", 0) >= MIN_VOLUME):
            filtered[coin_id] = coin_data
    return filtered

# Save filtered cryptocurrency prices to the database


async def save_prices_to_db(data: Any) -> None:
    try:
        if not data:
            logger.error("No data provided for saving prices.")
            return

        # Check if the data is in the expected format
        logger.info(f"Data to save: {data}")

        # Get MongoDB collection
        collection = await get_collection("prices")

        # Log the collection to ensure it's valid
        logger.info(f"Using collection: {collection}")

        # Insert data into the database
        result = await collection.insert_one({
            "data": data,
            "timestamp": datetime.now(timezone.utc)
        })

        logger.info(f"Prices saved successfully with id: {result.inserted_id}")
    except Exception as e:
        logger.exception("Failed to save prices to DB")


# Function to fetch social trends data from Reddit and store it in MongoDB


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
                                logger.info(
                                    f"Inserting/Updating: {social_entry_model.model_dump()}")
                                result = await collection.update_one(
                                    {"symbol": social_entry["symbol"],
                                        "platform": "Reddit"},
                                    # Use model_dump here
                                    {"$set": social_entry_model.model_dump()},
                                    upsert=True
                                )

                                logger.info(
                                    f"Update result: matched={result.matched_count}, modified={result.modified_count}")

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


async def filter_currencies_based_on_params(min_price: float, max_price: float) -> List[Dict]:
    """
    Fetch and filter cryptocurrencies based on specified parameters.
    """
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "price_change_percentage": "24h",
            "order": "market_cap_desc",
            "per_page": 250,
            "page": 1
        }

        # Fetching the coins data
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    # Filter cryptocurrencies based on criteria
                    filtered_coins = [
                        {
                            "id": coin["id"],
                            "symbol": coin["symbol"],
                            "name": coin["name"],
                            "current_price": coin["current_price"],
                            "market_cap": coin["market_cap"],
                            "total_volume": coin["total_volume"],
                            "price_change_percentage_24h": coin.get("price_change_percentage_24h", 0),
                            "timestamp": datetime.now(timezone.utc)
                        }
                        for coin in data
                        if min_price <= coin["current_price"] <= max_price
                        and coin["market_cap"] >= MIN_MARKET_CAP
                        and coin["total_volume"] >= MIN_VOLUME
                    ]

                    logger.info(
                        f"Filtered coins: {len(filtered_coins)} coins meet the criteria.")
                    return filtered_coins
                else:
                    logger.error(
                        f"Failed to fetch currencies. Status: {response.status}")
    except Exception as e:
        logger.exception("Error in filter_currencies_based_on_params")
    return []

# Store filtered cryptocurrencies in MongoDB


async def store_filtered_currencies(currencies: List[Dict], collection: Collection):
    """
    Store filtered cryptocurrencies in MongoDB.
    """
    try:
        if not currencies:
            logger.warning("No filtered currencies provided.")
            return

        # Bulk upsert operation for efficient updates
        operations = [
            {
                "updateOne": {
                    "filter": {"id": currency["id"]},
                    "update": {"$set": currency},
                    "upsert": True
                }
            }
            for currency in currencies
        ]

        if operations:
            result = await collection.bulk_write(operations)
            logger.info(f"Filtered currencies stored successfully. "
                        f"Matched: {result.matched_count}, Upserted: {result.upserted_count}.")
    except Exception as e:
        logger.exception("Failed to store filtered currencies")
