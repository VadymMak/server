import asyncio
from tasks.data_fetch import fetch_and_store_social_data


if __name__ == "__main__":
    asyncio.run(fetch_and_store_social_data())
