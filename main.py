from fastapi import FastAPI
from tasks.scheduler import init_scheduler, stop_scheduler
from db.database import get_database
from routes.prices import router as prices_router
from routes.social import router as social_router
from routes.investors import router as investors_router

app = FastAPI()

# Include routers with specific prefixes and tags
app.include_router(prices_router, prefix="/api", tags=["Prices"])
app.include_router(social_router, prefix="/api", tags=["Social"])
app.include_router(investors_router, prefix="/api", tags=["Investors"])


@app.on_event("startup")
async def on_startup():
    """
    Event triggered when the application starts.
    """
    init_scheduler()  # Call without await since it's not an async function
    try:
        db = await get_database()
        # Ping the database to ensure connection is successful
        await db.command("ping")
        app.state.db_connected = True
    except Exception as e:
        app.state.db_connected = False
        print(f"Error connecting to MongoDB: {e}")


@app.on_event("shutdown")
async def on_shutdown():
    """
    Event triggered when the application shuts down.
    """
    stop_scheduler()


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
