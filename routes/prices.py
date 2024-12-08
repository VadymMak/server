from fastapi import APIRouter, HTTPException, Query
from typing import List
# Ensure this model is properly defined
from models.price_model import PriceModel
from db.database import get_database  # Import the database connection function

router = APIRouter()


@router.get("/prices", response_model=List[PriceModel])
async def get_prices(
    symbol: str = Query(...,
                        description="The symbol of the cryptocurrency to fetch prices for."),
    min_price: float = Query(
        0, ge=0, description="The minimum price for filtering (default: 0)."),
    max_price: float = Query(
        0.1, gt=0, description="The maximum price for filtering (default: 0.1).")
):
    """
    Fetch price data for the specified cryptocurrency symbol with dynamic filtering for min/max price.
    """
    try:
        # Initialize the database connection
        db = get_database()

        # Build the query dynamically based on the provided filters
        query = {"symbol": symbol}
        if min_price is not None:
            query["price"] = {"$gte": min_price}
        if max_price is not None:
            query["price"] = query.get("price", {})
            query["price"]["$lte"] = max_price

        # Query MongoDB with the constructed filter
        prices_cursor = db.prices.find(query)
        prices_list = await prices_cursor.to_list(length=100)

        # Handle case where no data is found
        if not prices_list:
            raise HTTPException(
                status_code=404,
                detail=f"No price data found for the symbol: {symbol} with the given filters."
            )

        return prices_list

    except Exception as e:
        # Log the exception and return a server error response
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching price data."
        ) from e
