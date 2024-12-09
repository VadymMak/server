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

# Define async wrapper tasks


async def save_prices_to_db_task():
    data = await fetch_prices()
    await save_prices_to_db(data)


async def store_investor_data_task():
    data = await fetch_investors()
    await store_investor_data(data)


async def store_filtered_currencies_task():
    # Add min_price and max_price
    filtered_data = await filter_currencies_based_on_params(min_price=0.1, max_price=10)
    await store_filtered_currencies(filtered_data)

# Schedule tasks


def configure_scheduler():
    """
    Configures all scheduled jobs.
    """
    logger.debug("Configuring scheduler jobs...")

    # Add the min_price and max_price arguments to the filter_currencies job
    scheduler.add_job(fetch_prices, 'interval', minutes=10, id='fetch_prices')
    scheduler.add_job(fetch_and_store_social_data, 'interval',
                      minutes=10, id='fetch_social_data')
    scheduler.add_job(fetch_investors, 'interval',
                      minutes=10, id='fetch_investors')
    scheduler.add_job(filter_currencies_based_on_params,
                      'interval',  minutes=10, id='filter_currencies', args=[0, 1])  # Pass min_price, max_price here
    scheduler.add_job(save_prices_to_db_task, 'interval',
                      minutes=10, id='save_prices_to_db')
    scheduler.add_job(store_investor_data_task, 'interval',
                      minutes=10, id='store_investor_data')
    scheduler.add_job(store_filtered_currencies_task, 'interval',
                      minutes=10, id='store_filtered_currencies')

    logger.debug("Scheduler jobs configured successfully.")


async def start_scheduler():
    """
    Starts the scheduler within an asyncio event loop.
    """
    try:
        configure_scheduler()
        scheduler.start()
        logger.info("Scheduler started. Background tasks are running.")
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")


def stop_scheduler():
    """
    Stops the scheduler gracefully.
    """
    try:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped successfully.")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")

# Ensure that the scheduler runs asynchronously for FastAPI or standalone execution


def init_scheduler():
    """
    Initializes the scheduler to be called in a synchronous context.
    """
    asyncio.create_task(start_scheduler())


if __name__ == "__main__":
    # Start the scheduler in a standalone way
    asyncio.run(start_scheduler())
