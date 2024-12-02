from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class SocialModel(BaseModel):
    symbol: str
    platform: str
    followers: int
    engagement: float
    timestamp: datetime
    trend: Optional[str] = "Neutral"  # Default value for trend
    mentions: Optional[int] = 0  # Default value for mentions
    positive_sentiment: Optional[float] = 0.5  # Default sentiment
    date: Optional[datetime] = None  # Default value for date

    @field_validator("positive_sentiment")
    def check_sentiment_range(cls, v):
        if not (0 <= v <= 1):
            raise ValueError("positive_sentiment must be between 0 and 1.")
        return v
