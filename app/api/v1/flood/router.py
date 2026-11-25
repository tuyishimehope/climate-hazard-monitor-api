from typing import Annotated

from fastapi import APIRouter, Query

from app.service.flood import flood
from app.service.flood.schema import FloodParams

FLOOD_ROUTER = APIRouter(prefix="/api/v1/floods", tags=["floods"])


@FLOOD_ROUTER.get("")
async def get_floods_for_district(
    flood_query: Annotated[FloodParams, Query()]
):

    return await flood.query_the_precipitation(
        latitude=flood_query.latitude,
        longitude=flood_query.longitude,
        daily=flood_query.daily,
        timezone=flood_query.timezone,
        past_days=flood_query.past_days,
    )
