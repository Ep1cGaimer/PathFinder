# Deployment runbook

## Required accounts

- Google Cloud project with billing enabled and Maps, Routes, Geocoding, Cloud Run, Cloud Build, Artifact Registry, Storage, and Secret Manager APIs.
- Neon PostgreSQL project in AWS `us-east-1`, with PostGIS enabled and the pooled connection string.
- Upstash Redis database in `us-east-1` with TLS.
- Firebase project for Authentication and Hosting.
- Expo account owning the existing EAS project.

## Secrets and restrictions

Create separate Google credentials:

1. Browser key: restrict to the Firebase Hosting domains and Maps JavaScript API.
2. Android key: restrict to `com.epicgaimer.pathfinder`, the EAS release SHA-1, and Maps SDK for Android.
3. Server credential: keep in Secret Manager and restrict to Routes, Places/Geocoding, and Roads APIs actually enabled.

Store `DATABASE_URL`, `REDIS_URL`, `GOOGLE_MAPS_SERVER_API_KEY`, `GOOGLE_CLOUD_STORAGE_BUCKET`, and `FIREBASE_PROJECT_ID` as Cloud Run secrets/environment configuration. Never reuse the keys previously committed to the project; rotate them before release.

## First deployment

1. Install and authenticate the Google Cloud CLI.
2. Create the `pathfinder` Artifact Registry repository in `us-east1`.
3. Create a private Cloud Storage bucket with lifecycle and CORS rules for report images.
4. Run `gcloud builds submit --config cloudbuild.yaml .`.
5. Apply `alembic upgrade head` against Neon and run `python -m app.seed` once.
6. Set the Cloud Run URL as the GitHub `EXPO_PUBLIC_API_URL` variable.
7. Build the web export and deploy Firebase Hosting.
8. Run `npx eas build --platform android --profile preview` to publish an installable APK URL.

Cloud Run is configured for scale-to-zero, two maximum instances, one CPU, 2 GiB memory, and concurrency 20. Add billing alerts and API quotas before making the links public.

## Release

Run all CI checks, production smoke tests, and the production benchmark. Add verified URLs and results to the README, then tag `v1.0.0`. The tag triggers the keyless deployment workflow after GitHub Workload Identity Federation is configured.
