from db.database import get_database
from fastapi import APIRouter, HTTPException
from models.social_model import SocialModel
from pymongo import MongoClient
from pydantic import ValidationError
from typing import List

router = APIRouter()

# Подключение к базе данных
db = get_database()


@router.get("/social", response_model=List[SocialModel])
async def get_social_trends(symbol: str):
    """
    Получить данные социальных трендов для указанного символа криптовалюты.
    """
    # Fetch data based on the 'symbol' query parameter
    trends_cursor = db.social_trends.find({"symbol": symbol})

    # Convert the cursor to a list with a limit on the number of documents to fetch
    trends_list = await trends_cursor.to_list(length=100)

    if not trends_list:
        raise HTTPException(
            status_code=404, detail="Социальные тренды не найдены для указанного символа.")

    return trends_list


@router.post("/social", response_model=SocialModel)
async def create_social_trend(trend: SocialModel):
    try:
        # Insert the trend into the database
        inserted = await db.social_trends.insert_one(trend.dict())

        # Fetch the inserted document
        new_trend = await db.social_trends.find_one({"_id": inserted.inserted_id})

        # Check if the new trend is returned
        if new_trend is None:
            raise HTTPException(
                status_code=500, detail="Failed to insert data"
            )

        # Log the inserted data for debugging
        print(f"Inserted data: {new_trend}")

        return SocialModel(**new_trend)
    except ValidationError as e:
        print("Validation Error:", e.errors())
        raise HTTPException(
            status_code=422, detail=f"Validation error: {e.errors()}"
        )
