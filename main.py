from fastapi import FastAPI
from fastapi.lifespan import Lifespan
from tasks.scheduler import init_scheduler, stop_scheduler
from db.database import get_database
from routes.prices import router as prices_router
from routes.social import router as social_router
from routes.investors import router as investors_router


def lifespan(app: FastAPI):
    """
    Lifespan context manager for handling startup and shutdown events.
    """
    async def start():
        # Initialize the scheduler
        init_scheduler()
        try:
            # Connect to the database
            db = await get_database()
            await db.command("ping")  # Test the database connection
            app.state.db_connected = True
        except Exception as e:
            app.state.db_connected = False
            print(f"Error connecting to MongoDB: {e}")

    async def stop():
        # Stop the scheduler
        stop_scheduler()

    return start, stop


app = FastAPI(lifespan=lifespan)

# Include routers with specific prefixes and tags
app.include_router(prices_router, prefix="/api", tags=["Prices"])
app.include_router(social_router, prefix="/api", tags=["Social"])
app.include_router(investors_router, prefix="/api", tags=["Investors"])


@app.get("/")
async def read_root():
    """
    Root endpoint to test MongoDB connection.
    """
    if app.state.db_connected:
        return {"message": "Connected to MongoDB successfully!"}
    else:
        return {"error": "Failed to connect to MongoDB"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4500)
