from datetime import date

from pydantic import BaseModel


class DailyUsage(BaseModel):
    day: date
    calls: int
    weighted_calls: float
    failures: int
    daily_limit: int
    percent_of_limit: float


class UsageReport(BaseModel):
    provider: str
    source: str | None
    start: date
    end: date
    days: list[DailyUsage]
    total_calls: int
    total_weighted_calls: float
    total_failures: int
    month_weighted_calls: float
    monthly_limit: int
    daily_budget: float
