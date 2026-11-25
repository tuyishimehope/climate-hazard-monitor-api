import asyncio
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import func, select

from app.model.models import RainObservation
from app.service.rainfall.service import get_hazard, refresh_district

NOW = datetime(2026, 11, 25, 8, 0, tzinfo=UTC)  # 10:00 in Kigali, 25 Nov


def fake_open_meteo(requests: list):
    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "daily": {
                    "time": [
                        "2026-11-21",
                        "2026-11-22",
                        "2026-11-23",
                        "2026-11-24",
                        "2026-11-25",
                    ],
                    "precipitation_sum": [0.0, 30.0, 40.0, 35.0, 80.0],
                }
            },
        )

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def refresh(session, when=NOW, requests=None):
    client = fake_open_meteo([] if requests is None else requests)
    return asyncio.run(refresh_district(session, "gasabo", when, client=client))


def row_count(session):
    return session.scalar(select(func.count()).select_from(RainObservation))


def test_refresh_twice_creates_no_duplicates(session):
    refresh(session)
    first = row_count(session)
    refresh(session)
    assert first == 5
    assert row_count(session) == first


def test_refresh_sends_validated_params(session):
    seen = []
    refresh(session, requests=seen)
    params = dict(seen[0].url.params)
    assert params["daily"] == "precipitation_sum"
    assert params["past_days"] == "7"


def test_total_ignores_today_and_picks_the_rule(session):
    refresh(session)
    h = get_hazard(session, "gasabo", NOW)
    # 24th + 23rd + 22nd = 35 + 40 + 30 = 105 (today's 80 is not counted)
    assert h.rain_total_mm == 105.0
    assert h.level == "warning"
    assert ">= 100 mm = warning" in h.rule
    assert h.data_outdated is False
    assert "Not an official warning" in h.disclaimer


def test_data_outdated_when_older_than_24h(session):
    refresh(session, when=NOW - timedelta(hours=25))
    assert get_hazard(session, "gasabo", NOW).data_outdated is True


def test_not_outdated_just_under_24h(session):
    refresh(session, when=NOW - timedelta(hours=23, minutes=59))
    assert get_hazard(session, "gasabo", NOW).data_outdated is False


def test_no_data_returns_none(session):
    assert get_hazard(session, "gasabo", NOW) is None


def test_failed_fetch_keeps_old_data(session):
    refresh(session)
    bad = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(500))
    )
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(refresh_district(session, "gasabo", NOW, client=bad))
    assert row_count(session) == 5


def test_endpoint_returns_hazard(client, session):
    refresh(session, when=datetime.now(UTC))
    body = client.get("/api/v1/hazards/rainfall/gasabo").json()
    assert set(body) >= {"level", "rain_total_mm", "rule", "data_outdated"}


def test_endpoint_says_outdated_for_old_data(client, session):
    refresh(session, when=datetime.now(UTC) - timedelta(hours=30))
    body = client.get("/api/v1/hazards/rainfall/gasabo").json()
    assert body["data_outdated"] is True


def test_endpoint_unknown_district_and_no_data(client):
    assert client.get("/api/v1/hazards/rainfall/atlantis").status_code == 404
    assert client.get("/api/v1/hazards/rainfall/gasabo").status_code == 404
