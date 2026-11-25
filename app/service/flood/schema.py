from enum import Enum

from pydantic import BaseModel, Field


class DailyEnum(str, Enum):
    precipitation_sum = 'precipitation_sum'


class FloodParams(BaseModel):
    latitude: float = Field(default=-1.9223597189701973, ge=-90, le=90)
    longitude: float = Field(default=30.079777, ge=-180, le=180)
    daily: DailyEnum = DailyEnum.precipitation_sum
    timezone: str = "auto"
    past_days: int = 14
