from fastapi import APIRouter

from app.service.flood import flood

FLOOD_ROUTER = APIRouter(prefix="/api/v1/floods", tags=["floods"])


@FLOOD_ROUTER.get("")
def get_floods_for_district(
    latitude: float = -1.9223597189701973,
    longitude: float = 30.079777,
    daily: str = "precipitation_sum",
    timezone: str = "auto",
    past_days: int = 31,
):

    return flood.query_the_precipitation(
        latitude=latitude,
        longitude=longitude,
        daily=daily,
        timezone=timezone,
        past_days=past_days,
    )
