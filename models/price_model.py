from pydantic import BaseModel
from datetime import datetime


class PriceModel(BaseModel):
    symbol: str  # Symbol of the cryptocurrency
    price: float  # Current price of the cryptocurrency
    timestamp: datetime  # Timestamp when the price was recorded

class Config:
        orm_mode = True  # This tells Pydantic to treat it like an ORM model (for MongoDB in this case)