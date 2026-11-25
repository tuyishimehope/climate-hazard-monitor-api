from datetime import date, datetime

from pydantic import BaseModel

from app.service.rainfall.risk import Level


class RainfallHazard(BaseModel):
    district: str
    level: Level
    rain_total_mm: float | None
    window_start: date
    window_end: date
    rule: str
    data_updated_at: datetime
    data_outdated: bool
    disclaimer: str
