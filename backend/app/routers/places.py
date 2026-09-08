from fastapi import APIRouter, HTTPException, Query, Request

from ..services.cache import cache
from ..services.geo import geocoder

maps_client = geocoder

router = APIRouter(prefix="/places", tags=["places"])


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.get("/autocomplete")
async def autocomplete(request: Request, q: str = Query(min_length=2, max_length=120), session_token: str | None = None):
    client = _client_ip(request)
    if not cache.allow(f"places:{client}", limit=30, window_seconds=60):
        raise HTTPException(status_code=429, detail="Too many place searches")
    try:
        return {"suggestions": await maps_client.autocomplete(q, session_token)}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Search service unavailable") from exc

@router.get("/geocode")
async def geocode(request: Request, q: str = Query(min_length=2, max_length=160)):
    client = _client_ip(request)
    if not cache.allow(f"geocode:{client}", limit=20, window_seconds=60):
        raise HTTPException(status_code=429, detail="Too many location searches")
    try:
        result = await geocoder.geocode(q)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Search service unavailable") from exc
    if not result:
        raise HTTPException(status_code=404, detail="Location not found")
    return result
