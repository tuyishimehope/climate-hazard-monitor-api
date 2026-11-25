import logging
from datetime import date, datetime, timedelta, timezone

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.model.models import RainObservation
from app.service.rainfall import risk
from app.service.rainfall.client import fetch_daily_rain
from app.service.rainfall.districts import DISTRICTS
from app.service.rainfall.schema import RainfallHazard

log = logging.getLogger(__name__)

DISCLAIMER = "Not an official warning. Thresholds are uncalibrated placeholders."
LOCAL_TZ = timezone(timedelta(hours=2))
STALE_AFTER = timedelta(hours=24)
WINDOW_DAYS = 3


def upsert_days(
    session: Session, district: str, days: dict[date, float | None], now: datetime
) -> int:
    """Insert new days, update existing ones. Running twice adds no rows."""
    existing = {
        row.day: row
        for row in session.scalars(
            select(RainObservation).where(RainObservation.district == district)
        )
    }
    for day, mm in days.items():
        row = existing.get(day)
        if row is None:
            session.add(
                RainObservation(
                    district=district, day=day, precipitation_mm=mm, fetched_at=now
                )
            )
        else:
            row.precipitation_mm = mm
            row.fetched_at = now
    session.commit()
    return len(days)


async def refresh_district(
    session: Session,
    district: str,
    now: datetime,
    client: httpx.AsyncClient | None = None,
) -> int:
    lat, lon = DISTRICTS[district]
    raw = await fetch_daily_rain(lat, lon, client=client)
    days = {date.fromisoformat(k): v for k, v in raw.items()}
    n = upsert_days(session, district, days, now)
    log.info("refreshed district=%s days=%d", district, n)
    return n


def get_hazard(session: Session, district: str, now: datetime) -> RainfallHazard | None:
    """Build the F1 answer from stored data. Returns None if nothing stored yet."""
    last_fetch = session.scalar(
        select(func.max(RainObservation.fetched_at)).where(
            RainObservation.district == district
        )
    )
    if last_fetch is None:
        return None

    if last_fetch.tzinfo is None:
        last_fetch = last_fetch.replace(tzinfo=now.tzinfo)

    rows = session.scalars(
        select(RainObservation).where(RainObservation.district == district)
    )
    by_day = {r.day: r.precipitation_mm for r in rows}

    today = now.astimezone(LOCAL_TZ).date()
    days = risk.window_days(today, WINDOW_DAYS)
    total = risk.rain_total(by_day, days)
    watch, warning = settings.RAIN_WATCH_MM, settings.RAIN_WARNING_MM

    return RainfallHazard(
        district=district,
        level=risk.classify(total, watch, warning),
        rain_total_mm=total,
        window_start=min(days),
        window_end=max(days),
        rule=risk.rule_text(WINDOW_DAYS, watch, warning),
        data_updated_at=last_fetch,
        data_outdated=(now - last_fetch) > STALE_AFTER,
        disclaimer=DISCLAIMER,
    )
