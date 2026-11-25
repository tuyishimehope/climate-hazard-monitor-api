"""Daily job. Run: python -m app.jobs.refresh_rainfall  (cron / scheduler)."""

import asyncio
import logging
from datetime import UTC, datetime

from app.db.session import SessionLocal
from app.service.rainfall.districts import DISTRICTS
from app.service.rainfall.service import refresh_district

log = logging.getLogger("refresh_rainfall")


async def main() -> int:
    failures = 0
    with SessionLocal() as session:
        for district in DISTRICTS:
            try:
                await refresh_district(session, district, datetime.now(UTC))
            except Exception:  # one bad district must not stop the others
                failures += 1
                log.exception("refresh failed district=%s", district)
    return failures


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(1 if asyncio.run(main()) else 0)
