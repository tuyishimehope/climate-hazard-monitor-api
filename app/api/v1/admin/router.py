from datetime import UTC, date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.service.quota.schema import UsageReport
from app.service.quota.service import OPEN_METEO, usage_report

ADMIN_ROUTER = APIRouter(prefix="/api/v1/admin", tags=["admin"])

MAX_RANGE_DAYS = 92


@ADMIN_ROUTER.get("/api-usage", response_model=UsageReport)
def get_api_usage(
    session: Annotated[Session, Depends(get_session)],
    start: date | None = None,
    end: date | None = None,
    provider: Annotated[str, Query()] = OPEN_METEO,
    source: str | None = None,
) -> UsageReport:
    end = end or datetime.now(UTC).date()
    start = start or end - timedelta(days=6)
    if start > end:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "start must be <= end"
        )
    if (end - start).days + 1 > MAX_RANGE_DAYS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Range must be at most {MAX_RANGE_DAYS} days",
        )
    return usage_report(session, start, end, provider, source)
