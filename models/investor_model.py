from pydantic import BaseModel
from typing import Optional


class InvestorModel(BaseModel):
    coin_symbol: str
    investor_name: str
    investment_amount: float
    investment_type: str
    investment_date: str
