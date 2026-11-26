"""Daily job. Run: python -m app.jobs.purge_api_calls"""

import logging
from datetime import UTC, datetime, timedelta

from app.db.session import SessionLocal
from app.service.quota.service import purge_before

RETENTION = timedelta(days=180)

log = logging.getLogger("purge_api_calls")


def main() -> None:
    with SessionLocal() as session:
        deleted = purge_before(session, datetime.now(UTC) - RETENTION)
    log.info("purged api_calls rows=%d", deleted)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
