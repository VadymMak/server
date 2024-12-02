from fastapi import FastAPI
# Import the start_scheduler function
from tasks.scheduler import start_scheduler
from db.database import get_database
from routes.prices import router as prices_router  # Import the prices router
from routes.social import router as social_router  # Import the social router
# Import the investors router
from routes.investors import router as investors_router

app = FastAPI()

# Include routers with specific prefixes
app.include_router(prices_router, prefix="/api")
app.include_router(social_router, prefix="/api",
                   tags=["Social"])  # Updated prefix here
app.include_router(investors_router, prefix="/api", tags=["Investors"])

# Start the scheduler to run background tasks
start_scheduler()


@app.get("/")
async def read_root():
    """
    Root endpoint to test MongoDB connection.
    """
    try:
        db = await get_database()  # Use await to handle the async function
        # Optionally, check if the database connection works
        await db.command("ping")  # Send a ping command to verify connection
        return {"message": "Connected to MongoDB successfully!"}
    except Exception as e:
        return {"error": f"Failed to connect to MongoDB: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4500)
