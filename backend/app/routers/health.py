from fastapi import APIRouter
from sqlalchemy import text

from ..database import SessionLocal
from ..services.cache import cache

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict:
    database = "unavailable"
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        pass
    return {
        "status": "ok" if database == "ok" else "degraded",
        "version": "1.0.0",
        "database": database,
        "redis": "ok" if cache.ping() else "unavailable",
    }
