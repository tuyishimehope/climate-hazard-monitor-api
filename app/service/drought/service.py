import logging
from datetime import date, datetime, timedelta, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.model.models import DroughtAssessment
from app.service.drought.schema import DroughtStatus
from app.service.rainfall import risk
from app.service.rainfall.client import fetch_daily_rain
from app.service.rainfall.districts import DISTRICTS
from app.service.rainfall.risk import Level

log = logging.getLogger(__name__)

DROUGHT_MM = 20.0
WINDOW_DAYS = 30
LOCAL_TZ = timezone(timedelta(hours=2))
RULE = f"Rain total of the last {WINDOW_DAYS} full days: <= {DROUGHT_MM:g} mm = warning; otherwise normal."
DISCLAIMER = "Not an official warning. Thresholds are uncalibrated placeholders."


def classify(total_mm: float | None) -> Level:
    if total_mm is None:
        return Level.UNKNOWN
    return Level.WARNING if total_mm <= DROUGHT_MM else Level.NORMAL


def to_status(row: DroughtAssessment) -> DroughtStatus:
    return DroughtStatus(
        district=row.district,
        level=Level(row.level),
        rain_total_mm=row.rain_total_mm,
        window_start=row.window_start,
        window_end=row.window_end,
        rule=RULE,
        assessed_at=row.assessed_at,
        disclaimer=DISCLAIMER,
    )


def find(session: Session, district: str, window_end: date) -> DroughtAssessment | None:
    return session.scalar(
        select(DroughtAssessment).where(
            DroughtAssessment.district == district,
            DroughtAssessment.window_end == window_end,
        )
    )


def save(session: Session, values: dict[str, object]) -> DroughtAssessment:
    insert_stmt = insert(DroughtAssessment).values(**values)
    upsert = insert_stmt.on_conflict_do_update(
        index_elements=["district", "window_end"],
        set_={
            k: insert_stmt.excluded[k]
            for k in ("rain_total_mm", "level", "assessed_at")
        },
    ).returning(DroughtAssessment)
    row: DroughtAssessment = session.scalars(
        upsert, execution_options={"populate_existing": True}
    ).one()
    session.commit()
    return row


async def get_drought(
    session: Session,
    district: str,
    now: datetime,
    client: httpx.AsyncClient | None = None,
) -> DroughtStatus:
    days = risk.window_days(now.astimezone(LOCAL_TZ).date(), WINDOW_DAYS)
    window_end = max(days)

    stored = find(session, district, window_end)
    if stored is not None and stored.level != Level.UNKNOWN:
        return to_status(stored)

    lat, lon = DISTRICTS[district]
    raw = await fetch_daily_rain(
        lat, lon, past_days=WINDOW_DAYS, source="drought", client=client
    )
    by_day = {date.fromisoformat(k): v for k, v in raw.items()}
    total = risk.rain_total(by_day, days)

    row = save(
        session,
        {
            "district": district,
            "window_start": min(days),
            "window_end": window_end,
            "rain_total_mm": total,
            "level": classify(total).value,
            "assessed_at": now,
        },
    )
    log.info(
        "assessed drought district=%s total=%s level=%s", district, total, row.level
    )
    return to_status(row)
