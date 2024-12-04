import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

# Import all functions from data_fetch.py
from tasks.data_fetch import (
    fetch_prices,
    fetch_and_store_social_data,
    fetch_investors,
    filter_currencies_based_on_params,
    save_prices_to_db,
    store_investor_data,
    store_filtered_currencies,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the scheduler
scheduler = AsyncIOScheduler()

# Define wrapper tasks for functions requiring arguments


async def store_investor_data_task():
    data = await fetch_investors()  # Fetch required data dynamically
    await store_investor_data(data)


async def store_filtered_currencies_task():
    # Fetch required data dynamically
    filtered_data = await filter_currencies_based_on_params()
    await store_filtered_currencies(filtered_data)

# Schedule tasks
scheduler.add_job(fetch_prices, 'interval', minutes=10, id='fetch_prices')
scheduler.add_job(fetch_and_store_social_data, 'interval',
                  hours=1, id='fetch_social_data')
scheduler.add_job(fetch_investors, 'interval', hours=1, id='fetch_investors')
scheduler.add_job(filter_currencies_based_on_params,
                  'interval', hours=1, id='filter_currencies')
scheduler.add_job(store_investor_data_task, 'interval',
                  hours=1, id='store_investor_data')
scheduler.add_job(store_filtered_currencies_task, 'interval',
                  hours=1, id='store_filtered_currencies')
scheduler.add_job(save_prices_to_db, 'interval',
                  hours=1, id='save_prices_to_db')

# Start the scheduler


def start_scheduler():
    """
    Starts the scheduler to run the background tasks.
    """
    try:
        scheduler.start()
        logger.info(
            "Scheduler started. Fetching tasks are now running in the background.")
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")

# Stop the scheduler


def stop_scheduler():
    """
    Stops the scheduler gracefully.
    """
    try:
        if scheduler.running:
            scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped gracefully.")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")


# For testing locally
if __name__ == "__main__":
    try:
        start_scheduler()
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        stop_scheduler()
