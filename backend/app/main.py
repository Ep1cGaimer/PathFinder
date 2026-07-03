import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import health, places, reports, routes

settings = get_settings()
app = FastAPI(
    title="Pathfinder API",
    version="1.0.0",
    description="Crowdsourced road-quality route recommendations.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["Server-Timing"] = f"app;dur={elapsed_ms:.2f}"
    return response


app.include_router(health.router, prefix="/api/v1")
app.include_router(places.router, prefix="/api/v1")
app.include_router(routes.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
