from datetime import date, datetime

from sqlalchemy import DateTime, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RainObservation(Base):
    """One row = one district, one calendar day."""

    __tablename__ = "rain_observations"
    __table_args__ = (UniqueConstraint("district", "day"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    district: Mapped[str] = mapped_column(index=True)
    day: Mapped[date]
    precipitation_mm: Mapped[float | None] = mapped_column(Float)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
