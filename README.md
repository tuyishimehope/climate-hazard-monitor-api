# disaster-management-system-backend

## Setup

```bash
cp .env.example .env                       # set POSTGRES_PASSWORD
docker compose up -d --wait db             # Postgres + PostGIS on localhost:5432
uv sync
alembic upgrade head
python -m app.jobs.refresh_rainfall        # fetch + store rain (run daily)
uvicorn app.main:app --reload
curl localhost:8000/api/v1/hazards/rainfall/gasabo
```

Full stack in Docker (runs migrations on start):

```bash
docker compose up -d --build               # API_PORT=8010 to change host port
docker compose exec api python -m app.jobs.refresh_rainfall
```

## Database

Connection comes from `POSTGRES_*` in `.env`. Docker overrides only `POSTGRES_HOST=db`.

New migration: `alembic revision --autogenerate --rev-id v2 -m "describe change"`
→ `alembic/versions/v2_describe_change.py`.

## Rainfall level

Rain total of the last 3 full days. Thresholds (`RAIN_WATCH_MM`, `RAIN_WARNING_MM`)
are uncalibrated placeholders.

## Open-Meteo usage

Every Open-Meteo request is logged to `api_calls` with its weight (requests over
14 days count as more than one call). New calls are refused once today's weight
reaches `OPEN_METEO_DAILY_BUDGET` (default 8,000 of the 10,000 free daily calls).

```bash
curl "localhost:8000/api/v1/admin/api-usage?start=2026-11-01&end=2026-11-26&source=drought"
python -m app.jobs.purge_api_calls         # delete rows older than 180 days (run daily)
```

`/api/v1/admin/*` has no authentication yet. Do not expose it publicly.
