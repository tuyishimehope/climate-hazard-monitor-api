from datetime import date, datetime

from sqlalchemy import DateTime, Float, String, UniqueConstraint
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


class DroughtAssessment(Base):
    """One row = one district, one 30-day window ending yesterday."""

    __tablename__ = "drought_assessments"
    __table_args__ = (UniqueConstraint("district", "window_end"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    district: Mapped[str] = mapped_column(index=True)
    window_start: Mapped[date]
    window_end: Mapped[date]
    rain_total_mm: Mapped[float | None] = mapped_column(Float)
    level: Mapped[str] = mapped_column(String(16))
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
