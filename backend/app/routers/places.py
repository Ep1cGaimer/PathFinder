from fastapi import APIRouter, HTTPException, Query, Request

from ..services.cache import cache
from ..services.google_maps import maps_client

router = APIRouter(prefix="/places", tags=["places"])


@router.get("/autocomplete")
async def autocomplete(request: Request, q: str = Query(min_length=2, max_length=120), session_token: str | None = None):
    client = request.client.host if request.client else "unknown"
    if not cache.allow(f"places:{client}", limit=30, window_seconds=60):
        raise HTTPException(status_code=429, detail="Too many place searches")
    return {"suggestions": await maps_client.autocomplete(q, session_token)}

@router.get("/geocode")
async def geocode(request: Request, q: str = Query(min_length=2, max_length=160)):
    client = request.client.host if request.client else "unknown"
    if not cache.allow(f"geocode:{client}", limit=20, window_seconds=60):
        raise HTTPException(status_code=429, detail="Too many location searches")
    result = await maps_client.geocode(q)
    if not result:
        raise HTTPException(status_code=404, detail="Location not found")
    return result
