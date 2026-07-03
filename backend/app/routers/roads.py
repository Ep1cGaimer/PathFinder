from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.routing import nearby_quality_segments

router = APIRouter(prefix="/roads", tags=["roads"])


@router.get("/quality")
def road_quality(
    min_lat: float = Query(ge=-90, le=90),
    min_lng: float = Query(ge=-180, le=180),
    max_lat: float = Query(ge=-90, le=90),
    max_lng: float = Query(ge=-180, le=180),
    zoom: int = Query(default=13, ge=10, le=22),
    db: Session = Depends(get_db),
):
    if min_lat >= max_lat or min_lng >= max_lng:
        raise HTTPException(status_code=422, detail="Invalid map bounds")
    try:
        segments = nearby_quality_segments(db, min_lat, min_lng, max_lat, max_lng, zoom)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Road quality layer unavailable") from exc
    return {"segments": [segment.model_dump() for segment in segments]}
