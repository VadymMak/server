import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import time

# Import all functions from data_fetch.py
from tasks.data_fetch import (
    fetch_prices,
    fetch_and_store_social_data,
    fetch_investors,
    filter_currencies_based_on_params,
    save_prices_to_db,
    store_investor_data,
    store_filtered_currencies
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the scheduler
scheduler = BackgroundScheduler()

# Function to wrap async functions in a way that APScheduler can schedule them


def run_async(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # If there's already a running event loop, use create_task
        asyncio.create_task(func(*args, **kwargs))
    else:
        # Otherwise, run the async function in a new event loop
        asyncio.run(func(*args, **kwargs))


# Schedule your data fetching tasks
scheduler.add_job(run_async, 'interval', minutes=10,
                  id='fetch_prices', args=[fetch_prices])
scheduler.add_job(run_async, 'interval', hours=1,
                  id='fetch_social_data', args=[fetch_and_store_social_data])

# New tasks added for fetching investors and filtering currencies
scheduler.add_job(run_async, 'interval', hours=1,
                  id='fetch_investors', args=[fetch_investors])
scheduler.add_job(run_async, 'interval', hours=1, id='filter_currencies', args=[
                  filter_currencies_based_on_params])

# For saving prices to DB every hour
# Don't pass 'data' here. Let the function fetch the data dynamically when needed.
scheduler.add_job(run_async, 'interval', hours=1,
                  id='save_prices_to_db', args=[save_prices_to_db])

# Schedule tasks for storing investors and filtered currencies
scheduler.add_job(run_async, 'interval', hours=1,
                  id='store_investor_data', args=[store_investor_data])
scheduler.add_job(run_async, 'interval', hours=1,
                  id='store_filtered_currencies', args=[store_filtered_currencies])

# Function to start the scheduler


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

# Function to stop the scheduler gracefully


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


# For testing locally, use this block
if __name__ == "__main__":
    try:
        start_scheduler()
        while True:
            # Keep the script running to maintain the scheduler
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        stop_scheduler()
