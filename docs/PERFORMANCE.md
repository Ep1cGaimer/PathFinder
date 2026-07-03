# Performance evidence

No production number is claimed until this document contains a dated, reproducible result from the deployed stack.

## Scope

The resume threshold applies to Pathfinder's PostGIS route-enrichment query: sampling a candidate polyline, matching nearby road observations through the GiST geography index, and aggregating quality and coverage. It excludes Google Routes network time and mobile-to-server transit.

## Reproduce

```powershell
docker compose up -d
Set-Location backend
..\.venv\Scripts\alembic upgrade head
..\.venv\Scripts\python -m app.seed
..\.venv\Scripts\python scripts/benchmark_geospatial.py
```

Before release, seed at least 10,000 benchmark observations, run 100 warm iterations in the production region, and capture:

- UTC timestamp and deployed commit SHA
- PostgreSQL/PostGIS version and region
- observation count and route sample count
- p50, p95, and p99 in milliseconds
- `EXPLAIN (ANALYZE, BUFFERS)` output
- Redis warm-hit API latency at concurrency 50

## Release gate

- PostGIS route enrichment: p95 below 200 ms.
- Warm Redis recommendation: p95 below 100 ms.
- No numeric resume claim if either target is unverified or fails.

## Results

Pending production deployment. Local unit and CV golden tests pass; these do not substitute for a production latency measurement.
