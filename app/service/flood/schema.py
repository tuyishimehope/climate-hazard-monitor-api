from pydantic import BaseModel


class FloodRequest(BaseModel):
    latitude: float = -1.9223597189701973
    longitude: float = 30.079777
    daily: str = "precipitation_sum"
    timezone: str = "auto"
    past_days: int = 14
