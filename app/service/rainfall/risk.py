"""The rule. Pure functions: no database, no network, no clock. Easy to test."""

from datetime import date, timedelta
from enum import StrEnum


class Level(StrEnum):
    NORMAL = "normal"
    WATCH = "watch"
    WARNING = "warning"
    UNKNOWN = "unknown"  # not enough data to decide


def window_days(today: date, n: int) -> list[date]:
    """The n days before today (yesterday first)."""
    return [today - timedelta(days=i) for i in range(1, n + 1)]


def rain_total(by_day: dict[date, float | None], days: list[date]) -> float | None:
    """Sum rain over `days`. If any day is missing, return None (never guess)."""
    values = [by_day.get(d) for d in days]
    if any(v is None for v in values):
        return None
    return round(sum(v for v in values if v is not None), 1)


def classify(total_mm: float | None, watch_mm: float, warning_mm: float) -> Level:
    if total_mm is None:
        return Level.UNKNOWN
    if total_mm >= warning_mm:  # "at least" -> >=
        return Level.WARNING
    if total_mm >= watch_mm:
        return Level.WATCH
    return Level.NORMAL


def rule_text(n_days: int, watch_mm: float, warning_mm: float) -> str:
    return (
        f"Rain total of the last {n_days} full days: "
        f">= {warning_mm:g} mm = warning; "
        f">= {watch_mm:g} mm = watch; otherwise normal."
    )
