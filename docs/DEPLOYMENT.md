# Deployment runbook

Pathfinder uses GitHub Pages for the Expo web client, Render for the FastAPI API, PostgreSQL/PostGIS, and Valkey, and Supabase for authentication and report images.

## Automated web deployment

Pushes to `main` run `.github/workflows/deploy-open.yml`. The workflow exports Expo with the `/PathFinder` base path, deploys `mobile/dist-pages` to GitHub Pages, and publishes the backend image to GHCR.

Public build-time values:

- `EXPO_PUBLIC_API_URL`: the Render API URL ending in `/api/v1`
- `EXPO_PUBLIC_MAP_STYLE_URL`: `https://tiles.openfreemap.org/styles/liberty`
- `EXPO_PUBLIC_SUPABASE_URL`: the project URL
- `EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY`: the public client key

## Render API

The Render web service builds from the repository root:

```text
pip install -r backend/requirements.txt
```

It starts with:

```text
cd backend && alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT
```

Required server variables are documented in `.env.example`. `DATABASE_URL` and `VALKEY_URL` must use Render's internal connection strings. Keep Google research disabled in product traffic.

## Supabase

Configure the web client with the publishable key only. The API verifies Supabase JWTs through the project's JWKS endpoint. Report-image writes use the contributor's JWT; do not place a service-role key in the client or repository.

## Verification

After a deployment:

1. Open `/api/v1/health` and confirm database, cache, routing, and geocoding status.
2. Open the GitHub Pages site and confirm map tiles load beneath the controls.
3. Search for a destination and request a route.
4. Sign in, submit a report image, and confirm it appears in the reports layer.
5. Inspect Render logs for migration, memory, or provider-rate-limit errors.

Free services can cold-start, have quotas, and are not an uptime commitment. The free Render PostgreSQL database also has an expiration date shown in the Render dashboard.