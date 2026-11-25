from datetime import date

import pytest

from app.service.rainfall.risk import Level, classify, rain_total, window_days


@pytest.mark.parametrize(
    ("mm", "level"),
    [
        (0, Level.NORMAL),
        (49.9, Level.NORMAL),
        (50, Level.WATCH),  # "at least 50" includes 50
        (99.9, Level.WATCH),
        (100, Level.WARNING),  # boundary is inclusive
        (250, Level.WARNING),
        (None, Level.UNKNOWN),
    ],
)
def test_classify_boundaries(mm, level):
    assert classify(mm, watch_mm=50, warning_mm=100) == level


def test_window_is_the_three_days_before_today():
    assert window_days(date(2026, 11, 25), 3) == [
        date(2026, 11, 24),
        date(2026, 11, 23),
        date(2026, 11, 22),
    ]


def test_rain_total_adds_the_window_only():
    by_day = {
        date(2026, 11, 24): 10.0,
        date(2026, 11, 23): 5.5,
        date(2026, 11, 22): 1.0,
        date(2026, 11, 21): 999.0,
    }
    assert rain_total(by_day, window_days(date(2026, 11, 25), 3)) == 16.5


def test_missing_day_means_unknown_not_zero():
    by_day = {date(2026, 11, 24): 10.0, date(2026, 11, 23): None}
    assert rain_total(by_day, window_days(date(2026, 11, 25), 3)) is None
