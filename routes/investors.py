from fastapi import APIRouter, Query, HTTPException
from typing import List
from models.investor_model import InvestorModel
from db.database import get_database

router = APIRouter()


@router.get("/investors", response_model=List[InvestorModel])
async def get_investors(coin_symbol: str = Query(..., alias="coin_symbol")):
    """
    Возвращает список инвесторов для указанного символа монеты.
    """
    db = get_database()

    # Fetch investors data from the database (MongoDB)
    investors_cursor = db.investors.find({"coin_symbol": coin_symbol})
    investors_list = await investors_cursor.to_list(length=100)

    if not investors_list:
        raise HTTPException(
            status_code=404, detail="Инвесторы не найдены для указанного символа.")

    return investors_list


@router.post("/investors", response_model=InvestorModel)
async def create_investor(investor: InvestorModel):
    """
    Добавляет нового инвестора в базу данных для указанного символа монеты.
    """
    db = get_database()

    # Insert the new investor into the 'investors' collection
    result = await db.investors.insert_one(investor.dict())

    # Fetch the inserted investor from the database
    new_investor = await db.investors.find_one({"_id": result.inserted_id})

    if not new_investor:
        raise HTTPException(
            status_code=500, detail="Ошибка при добавлении инвестора.")

    return InvestorModel(**new_investor)
