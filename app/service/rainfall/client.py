import logging

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)


async def fetch_daily_rain(
    lat: float,
    lon: float,
    *,
    past_days: int = 7,
    client: httpx.AsyncClient | None = None,
) -> dict[str, float | None]:
    """Return {"2026-11-24": 12.3, ...} from Open-Meteo. Raises on any failure."""
    params: dict[str, str | int | float] = {
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_sum",
        "timezone": "Africa/Kigali",
        "past_days": past_days,
        "forecast_days": 1,
    }
    own_client = client is None
    client = client or httpx.AsyncClient(timeout=10.0)
    try:
        log.info("open-meteo call lat=%s lon=%s", lat, lon)
        response = await client.get(settings.OPEN_METEO_URL, params=params)
        response.raise_for_status()
        daily = response.json()["daily"]
        return dict(zip(daily["time"], daily["precipitation_sum"], strict=True))
    finally:
        if own_client:
            await client.aclose()
