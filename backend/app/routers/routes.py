from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import RouteRequest, RouteResponse
from ..services.cache import cache
from ..services.routing import recommend_routes

router = APIRouter(prefix="/routes", tags=["routes"])


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/recommend", response_model=RouteResponse)
async def recommend(request_body: RouteRequest, request: Request, db: Session = Depends(get_db)):
    client = _client_ip(request)
    if not cache.allow(f"routes:{client}", limit=20, window_seconds=60):
        raise HTTPException(status_code=429, detail="Too many route requests")
    try:
        response = await recommend_routes(request_body, db)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Routing service unavailable") from exc
    if not response.routes:
        raise HTTPException(status_code=404, detail="No routes found")
    return response
