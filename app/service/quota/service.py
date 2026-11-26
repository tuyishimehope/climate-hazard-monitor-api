import logging
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import Date, cast, delete, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.model.models import ApiCall
from app.service.quota.schema import DailyUsage, UsageReport

log = logging.getLogger(__name__)

OPEN_METEO = "open-meteo"


class QuotaExceededError(Exception):
    pass


def call_weight(days: int, variables: int) -> float:
    return round(max(1.0, days / 14) * max(1.0, variables / 10), 2)


def start_of_day(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=UTC)


def weight_since(session: Session, since: datetime, provider: str) -> float:
    total = session.scalar(
        select(func.coalesce(func.sum(ApiCall.weight), 0.0)).where(
            ApiCall.provider == provider, ApiCall.called_at >= since
        )
    )
    return float(total or 0.0)


def ensure_budget(weight: float, provider: str = OPEN_METEO) -> None:
    today = start_of_day(datetime.now(UTC).date())
    with SessionLocal() as session:
        used = weight_since(session, today, provider)
    if used + weight > settings.OPEN_METEO_DAILY_BUDGET:
        raise QuotaExceededError(
            f"{provider} daily budget reached ({used:g}/{settings.OPEN_METEO_DAILY_BUDGET:g})"
        )


def record_call(
    *,
    source: str,
    called_at: datetime,
    status_code: int | None,
    weight: float,
    duration_ms: int,
    provider: str = OPEN_METEO,
) -> None:
    ok = status_code is not None and status_code < 400
    try:
        with SessionLocal() as session:
            session.add(
                ApiCall(
                    provider=provider,
                    source=source,
                    called_at=called_at,
                    status_code=status_code,
                    ok=ok,
                    weight=weight,
                    duration_ms=duration_ms,
                )
            )
            session.commit()
    except Exception:
        log.exception(
            "failed to record api call provider=%s source=%s", provider, source
        )


def usage_report(
    session: Session,
    start: date,
    end: date,
    provider: str = OPEN_METEO,
    source: str | None = None,
) -> UsageReport:
    day = cast(func.timezone("UTC", ApiCall.called_at), Date)
    stmt = (
        select(
            day,
            func.count(),
            func.sum(ApiCall.weight),
            func.count().filter(ApiCall.ok.is_(False)),
        )
        .where(
            ApiCall.provider == provider,
            ApiCall.called_at >= start_of_day(start),
            ApiCall.called_at < start_of_day(end + timedelta(days=1)),
        )
        .group_by(day)
    )
    if source is not None:
        stmt = stmt.where(ApiCall.source == source)
    found = {row[0]: row for row in session.execute(stmt)}

    limit = settings.OPEN_METEO_DAILY_LIMIT
    days: list[DailyUsage] = []
    for i in range((end - start).days + 1):
        d = start + timedelta(days=i)
        _, calls, weighted, failures = found.get(d, (d, 0, 0.0, 0))
        weighted = round(float(weighted or 0.0), 2)
        days.append(
            DailyUsage(
                day=d,
                calls=calls,
                weighted_calls=weighted,
                failures=failures,
                daily_limit=limit,
                percent_of_limit=round(100 * weighted / limit, 2),
            )
        )

    today = datetime.now(UTC).date()
    month_used = round(
        weight_since(session, start_of_day(today.replace(day=1)), provider), 2
    )
    return UsageReport(
        provider=provider,
        source=source,
        start=start,
        end=end,
        days=days,
        total_calls=sum(d.calls for d in days),
        total_weighted_calls=round(sum(d.weighted_calls for d in days), 2),
        total_failures=sum(d.failures for d in days),
        month_weighted_calls=month_used,
        monthly_limit=settings.OPEN_METEO_MONTHLY_LIMIT,
        daily_budget=settings.OPEN_METEO_DAILY_BUDGET,
    )


def purge_before(session: Session, cutoff: datetime) -> int:
    result = session.execute(delete(ApiCall).where(ApiCall.called_at < cutoff))
    session.commit()
    return int(getattr(result, "rowcount", 0) or 0)
