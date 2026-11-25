import requests

from app.service.http_client.client import ApiClient


async def query_the_precipitation(
    latitude: float,
    longitude: float,
    daily: str,
    timezone: str = "auto",
    past_days: int = 31,
):
    session = await ApiClient().init_client()
    response = await session.get(f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&daily={daily}&timezone={timezone}&past_days={past_days}")
    # filter
    # store result
    return response.json()
