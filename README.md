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
