import enum
from datetime import date, datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

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


class ApiCall(Base):
    """One row = one HTTP request to an external API."""

    __tablename__ = "api_calls"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(32))
    source: Mapped[str] = mapped_column(String(32))
    called_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status_code: Mapped[int | None]
    ok: Mapped[bool]
    weight: Mapped[float] = mapped_column(Float)
    duration_ms: Mapped[int] = mapped_column(Integer)


class User(Base):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str | None]
    last_name: Mapped[str | None]
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, server_default=func.now()
    )

    sessions: Mapped[list[UserSession]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )


class SessionStatus(enum.StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    token_hash: Mapped[str] = mapped_column(unique=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_account.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[SessionStatus] = mapped_column(default=SessionStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="sessions")
