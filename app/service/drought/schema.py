from datetime import date, datetime

from pydantic import BaseModel

from app.service.rainfall.risk import Level


class DroughtStatus(BaseModel):
    district: str
    level: Level
    rain_total_mm: float | None
    window_start: date
    window_end: date
    rule: str
    assessed_at: datetime
    disclaimer: str
