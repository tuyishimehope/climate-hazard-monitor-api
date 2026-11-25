from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.service.rainfall import service
from app.service.rainfall.districts import DISTRICTS
from app.service.rainfall.schema import RainfallHazard

RAINFALL_ROUTER = APIRouter(prefix="/api/v1/hazards/rainfall", tags=["rainfall"])


@RAINFALL_ROUTER.get("/{district}", response_model=RainfallHazard)
def get_rainfall_hazard(
    district: str, session: Annotated[Session, Depends(get_session)]
) -> RainfallHazard:
    district = district.lower()
    if district not in DISTRICTS:
        raise HTTPException(404, f"Unknown district. Known: {sorted(DISTRICTS)}")
    hazard = service.get_hazard(session, district, datetime.now(UTC))
    if hazard is None:
        raise HTTPException(
            404, "No rainfall data stored yet. Run: python -m app.jobs.refresh_rainfall"
        )
    return hazard
