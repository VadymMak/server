from apscheduler.schedulers.background import BackgroundScheduler
from tasks.data_fetch import fetch_prices, fetch_and_store_social_data
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

# Schedule your data fetching tasks
scheduler.add_job(lambda: asyncio.run(fetch_prices()),
                  'interval', minutes=10, id='fetch_prices')
scheduler.add_job(lambda: asyncio.run(fetch_and_store_social_data()),
                  'interval', hours=1, id='fetch_social_data')


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
            asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        stop_scheduler()
