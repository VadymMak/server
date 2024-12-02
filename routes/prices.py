from fastapi import APIRouter, HTTPException
from typing import List
# Ensure this model is defined correctly
from models.price_model import PriceModel
from db.database import get_database  # Import the get_database function

router = APIRouter()


@router.get("/prices", response_model=List[PriceModel])
async def get_prices(symbol: str):
    """
    Получить данные цен для указанного символа криптовалюты.
    """
    # Initialize the database connection
    db = get_database()  # No need to await here

    # Fetching prices from MongoDB
    prices_cursor = db.prices.find({"symbol": symbol})
    prices_list = await prices_cursor.to_list(length=100)

    if not prices_list:
        raise HTTPException(
            status_code=404, detail="Цены не найдены для указанного символа.")

    return prices_list
