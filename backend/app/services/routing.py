import hashlib
import json

import polyline
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import get_settings
from ..schemas import RouteOption, RouteRequest, RouteResponse
from .cache import cache
from .google_maps import CandidateRoute, maps_client

QUALITY_SQL = text(
    """
    WITH route AS (
      SELECT ST_Segmentize(ST_GeogFromText(:route_wkt), 50)::geometry AS geom
    ), samples AS (
      SELECT (ST_DumpPoints(geom)).geom AS geom FROM route
    ), matched AS (
      SELECT s.geom,
        (SELECT a.road_quality
         FROM road_reports r
         JOIN road_assessments a ON a.report_id = r.id
         WHERE r.status = 'ready'
           AND ST_DWithin(r.geom, s.geom::geography, :radius)
         ORDER BY ST_Distance(r.geom, s.geom::geography), r.created_at DESC
         LIMIT 1) AS quality
      FROM samples s
    )
    SELECT COALESCE(AVG(quality), 50.0) AS observed_quality,
           COALESCE(COUNT(quality)::float / NULLIF(COUNT(*), 0), 0.0) AS coverage
    FROM matched
    """
)


def cache_key(request: RouteRequest, version: int) -> str:
    payload = {
        "o": [round(request.origin.latitude, 5), round(request.origin.longitude, 5)],
        "d": [round(request.destination.latitude, 5), round(request.destination.longitude, 5)],
        "v": version,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]
    return f"pathfinder:routes:{digest}"


def score_candidates(candidates: list[CandidateRoute], qualities: list[tuple[float, float]]) -> list[RouteOption]:
    if not candidates:
        return []
    min_distance = min(route.distance_meters for route in candidates)
    min_duration = min(route.duration_seconds for route in candidates)
    options = []
    for index, (route, (observed, coverage)) in enumerate(zip(candidates, qualities, strict=True)):
        coverage = max(0.0, min(1.0, coverage))
        effective_quality = 50 + coverage * (observed - 50)
        distance_score = min_distance / max(route.distance_meters, 1) * 100
        duration_score = min_duration / max(route.duration_seconds, 1) * 100
        final = 0.25 * distance_score + 0.35 * duration_score + 0.40 * effective_quality
        options.append(
            RouteOption(
                id=f"route-{index + 1}", summary=route.summary,
                encoded_polyline=route.encoded_polyline,
                distance_meters=route.distance_meters, duration_seconds=route.duration_seconds,
                road_quality=round(effective_quality, 1), quality_coverage=round(coverage, 3),
                pathfinder_score=round(final, 1),
            )
        )
    options.sort(key=lambda item: item.pathfinder_score, reverse=True)
    options[0].is_recommended = True
    return options


def route_wkt(encoded: str) -> str:
    coordinates = polyline.decode(encoded)
    points = ",".join(f"{longitude} {latitude}" for latitude, longitude in coordinates)
    return f"SRID=4326;LINESTRING({points})"


async def recommend_routes(request: RouteRequest, db: Session) -> RouteResponse:
    version = cache.data_version()
    key = cache_key(request, version)
    cached = cache.get_json(key)
    if cached:
        cached["cache_status"] = "hit"
        return RouteResponse.model_validate(cached)
    candidates = await maps_client.routes(request.origin, request.destination)
    qualities: list[tuple[float, float]] = []
    database_available = True
    for candidate in candidates:
        if not database_available:
            qualities.append((50.0, 0.0))
            continue
        try:
            row = db.execute(QUALITY_SQL, {"route_wkt": route_wkt(candidate.encoded_polyline), "radius": get_settings().route_quality_radius_meters}).one()
            qualities.append((float(row.observed_quality), float(row.coverage)))
        except Exception:
            db.rollback()
            qualities.append((50.0, 0.0))
            database_available = False
    response = RouteResponse(routes=score_candidates(candidates, qualities), cache_status="miss", road_data_version=version)
    cache.set_json(key, response.model_dump(), get_settings().route_cache_ttl_seconds)
    return response
