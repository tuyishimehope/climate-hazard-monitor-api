from datetime import UTC, datetime
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.service.drought.schema import DroughtStatus
from app.service.drought.service import get_drought
from app.service.rainfall.districts import DISTRICTS

DROUGHT_ROUTER = APIRouter(prefix="/api/v1/hazards/drought", tags=["drought"])


@DROUGHT_ROUTER.get("/{district}", response_model=DroughtStatus)
async def get_drought_status(
    district: str, session: Annotated[Session, Depends(get_session)]
) -> DroughtStatus:
    district = district.lower()
    if district not in DISTRICTS:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Unknown district. Known: {sorted(DISTRICTS)}"
        )
    try:
        return await get_drought(session, district, datetime.now(UTC))
    except httpx.HTTPError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Rainfall provider is unavailable. Try again later.",
        ) from exc
