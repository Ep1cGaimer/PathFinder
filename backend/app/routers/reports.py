import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..config import get_settings
from ..database import get_db
from ..models import ReportStatus, RoadAssessment, RoadReport, User
from ..services.auth import AuthenticatedUser, require_user
from ..services.cache import cache
from ..services.road_network import snap_to_road
from ..services.storage import image_storage
from ..services.vision import vision_model

router = APIRouter(prefix="/reports", tags=["reports"])
ALLOWED_IMAGES = {"image/jpeg", "image/png", "image/webp", "image/avif"}


def serialize(report: RoadReport) -> dict:
    assessment = report.assessment
    payload = {
        "id": str(report.id), "latitude": report.latitude, "longitude": report.longitude,
        "description": report.description, "status": report.status.value,
        "road_place_id": report.road_place_id, "snap_status": report.snap_status,
        "snapped_location": (
            {"latitude": report.snapped_latitude, "longitude": report.snapped_longitude}
            if report.snapped_latitude is not None and report.snapped_longitude is not None
            else None
        ),
        "is_demo": report.is_demo, "created_at": report.created_at,
        "image_url": f"/api/v1/reports/{report.id}/image" if report.image_key else None,
        "assessment": None if not assessment else {
            "model_version": assessment.model_version, "detections": assessment.detections,
            "surface_damage": assessment.surface_damage,
            "traffic_safety_risk": assessment.traffic_safety_risk,
            "ride_discomfort": assessment.ride_discomfort,
            "waterlogging": assessment.waterlogging,
            "urgency_for_repair": assessment.urgency_for_repair,
            "road_quality": assessment.road_quality, "confidence": assessment.confidence,
        },
    }
    payload['road_segment_id'] = report.road_segment_id
    payload['snap_distance_meters'] = report.snap_distance_meters
    return payload


@router.get("")
def list_reports(
    min_lat: float, min_lng: float, max_lat: float, max_lng: float,
    db: Session = Depends(get_db),
):
    if min_lat >= max_lat or min_lng >= max_lng:
        raise HTTPException(status_code=422, detail="Invalid map bounds")
    try:
        reports = db.scalars(
            select(RoadReport).options(joinedload(RoadReport.assessment)).where(
                RoadReport.status == ReportStatus.READY,
                RoadReport.latitude.between(min_lat, max_lat),
                RoadReport.longitude.between(min_lng, max_lng),
            ).order_by(RoadReport.created_at.desc()).limit(300)
        ).all()
    except Exception as exc:
        db.rollback()
        if get_settings().app_env != "development":
            raise HTTPException(status_code=503, detail="Road observations unavailable") from exc
        reports = []
    return {"reports": [serialize(report) for report in reports]}


@router.post("", status_code=201)
async def create_report(
    latitude: float = Form(...), longitude: float = Form(...),
    description: str = Form(default=""), image: UploadFile = File(...),
    user: AuthenticatedUser = Depends(require_user), db: Session = Depends(get_db),
):
    if image.content_type not in ALLOWED_IMAGES:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, WebP, or AVIF image")
    contents = await image.read(10 * 1024 * 1024 + 1)
    if not contents or len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be between 1 byte and 10 MB")
    account = db.get(User, user.id)
    if not account:
        account = User(id=user.id, name=user.name)
        db.add(account)
    snapped = snap_to_road(db, latitude, longitude)
    report = RoadReport(
        user_id=user.id,
        latitude=latitude,
        longitude=longitude,
        snapped_latitude=snapped.latitude if snapped else None,
        snapped_longitude=snapped.longitude if snapped else None,
        road_place_id=f'osm-way:{snapped.osm_way_id}' if snapped else None,
        road_segment_id=snapped.segment_id if snapped else None,
        snap_distance_meters=snapped.distance_meters if snapped else None,
        snap_status="snapped" if snapped else "fallback",
        description=description[:1000],
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    suffix = Path(image.filename or "report.jpg").suffix or ".jpg"
    image_key = f"reports/{report.id}{suffix.lower()}"
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temporary:
            temporary.write(contents)
            temporary_path = Path(temporary.name)
        assessment = await run_in_threadpool(vision_model.assess, temporary_path)
        await run_in_threadpool(image_storage.put, image_key, contents, image.content_type, user.token)
        report.image_key = image_key
        report.status = ReportStatus.READY
        report.assessment = RoadAssessment(report_id=report.id, **assessment)
        db.commit()
        db.refresh(report)
        cache.bump_data_version()
        return serialize(report)
    except Exception as exc:
        report.status = ReportStatus.FAILED
        db.commit()
        raise HTTPException(status_code=422, detail="Road assessment failed") from exc
    finally:
        if temporary_path:
            temporary_path.unlink(missing_ok=True)


@router.get("/me")
def my_reports(user: AuthenticatedUser = Depends(require_user), db: Session = Depends(get_db)):
    reports = db.scalars(
        select(RoadReport).options(joinedload(RoadReport.assessment))
        .where(RoadReport.user_id == user.id).order_by(RoadReport.created_at.desc())
    ).all()
    return {"reports": [serialize(report) for report in reports]}


@router.get("/{report_id}/image")
def report_image(report_id: uuid.UUID, db: Session = Depends(get_db)):
    report = db.get(RoadReport, report_id)
    if not report or not report.image_key:
        raise HTTPException(status_code=404, detail="Image not found")
    try:
        return Response(image_storage.get(report.image_key), media_type="image/jpeg", headers={"Cache-Control": "public, max-age=3600"})
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Image not found") from exc
