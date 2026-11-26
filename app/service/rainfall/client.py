import logging
import time
from datetime import UTC, datetime

import httpx

from app.core.config import settings
from app.service.quota.service import call_weight, ensure_budget, record_call

log = logging.getLogger(__name__)

VARIABLES = ["precipitation_sum"]
FORECAST_DAYS = 1


async def fetch_daily_rain(
    lat: float,
    lon: float,
    *,
    source: str,
    past_days: int = 7,
    client: httpx.AsyncClient | None = None,
) -> dict[str, float | None]:
    """Return {"2026-11-24": 12.3, ...} from Open-Meteo. Raises on any failure."""
    params: dict[str, str | int | float] = {
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join(VARIABLES),
        "timezone": "Africa/Kigali",
        "past_days": past_days,
        "forecast_days": FORECAST_DAYS,
    }
    weight = call_weight(past_days + FORECAST_DAYS, len(VARIABLES))
    ensure_budget(weight)

    own_client = client is None
    client = client or httpx.AsyncClient(timeout=10.0)
    called_at = datetime.now(UTC)
    started = time.perf_counter()
    status_code: int | None = None
    try:
        log.info("open-meteo call source=%s lat=%s lon=%s", source, lat, lon)
        response = await client.get(settings.OPEN_METEO_URL, params=params)
        status_code = response.status_code
        response.raise_for_status()
        daily = response.json()["daily"]
        return dict(zip(daily["time"], daily["precipitation_sum"], strict=True))
    finally:
        record_call(
            source=source,
            called_at=called_at,
            status_code=status_code,
            weight=weight,
            duration_ms=round((time.perf_counter() - started) * 1000),
        )
        if own_client:
            await client.aclose()
