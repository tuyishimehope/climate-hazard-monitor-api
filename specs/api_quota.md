# API quota (Open-Meteo usage)

1. Goal: know how many Open-Meteo calls we make per day, and stop before the free limit.
   Free tier: 600/min, 5,000/hour, 10,000/day, 300,000/month (non-commercial only).
   Open-Meteo has no quota header or usage endpoint, so we count ourselves.

2. Weight: Open-Meteo counts long requests as several calls.
   More than 14 days or more than 10 variables for one location = more than 1 call.
   weight = max(1, days / 14) * max(1, variables / 10)   (inferred from their examples)
   days = past_days + forecast_days
   Rainfall refresh: 7 + 1 days, 1 variable -> 1.0
   Drought: 30 + 1 days, 1 variable -> 2.2

3. Storage: one INSERT per HTTP request (append-only log). Never read-then-update.
   Table api_calls:
     id, provider ("open-meteo"), source ("rainfall" | "drought"),
     called_at (timestamptz, indexed), status_code (null on network error),
     ok (bool), weight (float), duration_ms (int)

4. Rules:
   - Record every request, including failures and timeouts (record in `finally`).
   - Record in its own session and commit, so the log survives if the feature rolls back.
   - The HTTP client does not receive a DB session from callers.
   - A failure to record logs an error but never breaks the feature.

5. Guard (optional, step 2):
   Before a request, sum today's weight (UTC day).
   If sum + weight > DAILY_BUDGET (default 8,000 = 80% of 10,000) -> refuse.
   Feature returns 503 "Rainfall provider quota reached". Stored data is still served.
   Small race between check and insert is accepted.

6. Admin endpoint:
   GET /api/v1/admin/api-usage?start=2026-11-01&end=2026-11-26&provider=open-meteo&source=drought
   Defaults: last 7 days, all providers, all sources. Max range 92 days.
   Response, one row per UTC day (days with no calls included as 0):
     { "day": "2026-11-26", "calls": 41, "weighted_calls": 63.4, "failures": 2,
       "daily_limit": 10000, "percent_of_limit": 0.6 }
   Plus totals for the range and the current month (against 300,000).
   Must not be public: protect before deploying (no auth exists yet).

7. Retention: delete rows older than 180 days (daily job). Max 10k rows/day.

8. Acceptance (manual):
   - One drought request with no stored row -> 1 row, weight 2.2.
   - Second drought request (served from table) -> no new row.
   - Open-Meteo down -> 1 row with ok=false, endpoint still returns 502.
   - Admin endpoint for today shows the counts above.
   - Budget set to 1 -> next request refused with 503, no Open-Meteo call made.
