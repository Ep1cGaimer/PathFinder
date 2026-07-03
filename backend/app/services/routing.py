import hashlib
import json
import math

import polyline
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import get_settings
from ..schemas import RoadQualitySegment, RouteOption, RouteRequest, RouteResponse
from .cache import cache
from .geo import CandidateRoute, routing_provider

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
           AND ST_DWithin(r.effective_geom, s.geom::geography, :radius)
         ORDER BY ST_Distance(r.effective_geom, s.geom::geography), r.created_at DESC
         LIMIT 1) AS quality
      FROM samples s
    )
    SELECT COALESCE(AVG(quality), 50.0) AS observed_quality,
           COALESCE(COUNT(quality)::float / NULLIF(COUNT(*), 0), 0.0) AS coverage
    FROM matched
    """
)

SEGMENT_QUALITY_SQL = text(
    """
    WITH input_segments AS (
      SELECT ordinal, ST_GeogFromText(wkt) AS geom
      FROM jsonb_to_recordset(CAST(:segments AS jsonb)) AS value(ordinal integer, wkt text)
    ), scored AS (
      SELECT segment.ordinal,
        observation.road_quality,
        observation.confidence,
        observation.weight
      FROM input_segments segment
      LEFT JOIN LATERAL (
        SELECT assessment.road_quality,
          assessment.confidence,
          assessment.confidence
            * EXP(-ST_Distance(report.effective_geom, segment.geom) / :radius)
            * EXP(-EXTRACT(EPOCH FROM (now() - report.created_at)) / 15552000.0) AS weight
        FROM road_reports report
        JOIN road_assessments assessment ON assessment.report_id = report.id
        WHERE report.status = 'ready'
          AND ST_DWithin(report.effective_geom, segment.geom, :radius)
      ) observation ON TRUE
    )
    SELECT ordinal,
      SUM(road_quality * weight) / NULLIF(SUM(weight), 0) AS road_quality,
      COUNT(road_quality)::integer AS observation_count,
      SUM(confidence * weight) / NULLIF(SUM(weight), 0) AS confidence
    FROM scored
    GROUP BY ordinal
    ORDER BY ordinal
    """
)

STORE_SEGMENTS_SQL = text(
    """
    INSERT INTO road_segments (segment_hash, encoded_polyline, geom)
    SELECT segment_hash, encoded_polyline, ST_GeogFromText(wkt)
    FROM jsonb_to_recordset(CAST(:segments AS jsonb))
      AS value(segment_hash varchar, encoded_polyline text, wkt text)
    ON CONFLICT (segment_hash) DO UPDATE
      SET encoded_polyline = EXCLUDED.encoded_polyline,
          last_seen_at = now()
    """
)

NEARBY_SEGMENTS_SQL = text(
    """
    WITH visible AS (
      SELECT segment_hash, encoded_polyline, geom
      FROM road_segments
      WHERE ST_Intersects(
        geom,
        ST_MakeEnvelope(:min_lng, :min_lat, :max_lng, :max_lat, 4326)::geography
      )
      ORDER BY last_seen_at DESC
      LIMIT :limit
    )
    SELECT visible.segment_hash,
      visible.encoded_polyline,
      SUM(observation.road_quality * observation.weight) / NULLIF(SUM(observation.weight), 0) AS road_quality,
      COUNT(observation.road_quality)::integer AS observation_count,
      SUM(observation.confidence * observation.weight) / NULLIF(SUM(observation.weight), 0) AS confidence
    FROM visible
    LEFT JOIN LATERAL (
      SELECT assessment.road_quality,
        assessment.confidence,
        assessment.confidence
          * EXP(-ST_Distance(report.effective_geom, visible.geom) / :radius)
          * EXP(-EXTRACT(EPOCH FROM (now() - report.created_at)) / 15552000.0) AS weight
      FROM road_reports report
      JOIN road_assessments assessment ON assessment.report_id = report.id
      WHERE report.status = 'ready'
        AND ST_DWithin(report.effective_geom, visible.geom, :radius)
    ) observation ON TRUE
    GROUP BY visible.segment_hash, visible.encoded_polyline
    HAVING COUNT(observation.road_quality) > 0
    """
)


OSM_SEGMENT_QUALITY_SQL = text('''
    WITH input_segments AS (
      SELECT ordinal, ST_GeomFromEWKT(wkt) AS geom
      FROM jsonb_to_recordset(CAST(:segments AS jsonb)) AS value(ordinal integer, wkt text)
    ), matched_roads AS (
      SELECT input.ordinal, road.segment_id
      FROM input_segments input
      LEFT JOIN LATERAL (
        SELECT segment_id
        FROM osm_road_segments
        WHERE ST_DWithin(geom::geography, input.geom::geography, :radius)
        ORDER BY geom <-> ST_Centroid(input.geom)
        LIMIT 1
      ) road ON TRUE
    )
    SELECT matched.ordinal,
      SUM(assessment.road_quality * assessment.confidence)
        / NULLIF(SUM(assessment.confidence), 0) AS road_quality,
      COUNT(assessment.road_quality)::integer AS observation_count,
      AVG(assessment.confidence) AS confidence
    FROM matched_roads matched
    LEFT JOIN road_reports report
      ON report.road_segment_id = matched.segment_id AND report.status = 'ready'
    LEFT JOIN road_assessments assessment ON assessment.report_id = report.id
    GROUP BY matched.ordinal
    ORDER BY matched.ordinal
''')

OSM_NEARBY_SEGMENTS_SQL = text('''
    SELECT road.segment_id,
      ST_AsEncodedPolyline(road.geom, 5) AS encoded_polyline,
      SUM(assessment.road_quality * assessment.confidence)
        / NULLIF(SUM(assessment.confidence), 0) AS road_quality,
      COUNT(assessment.road_quality)::integer AS observation_count,
      AVG(assessment.confidence) AS confidence
    FROM osm_road_segments road
    JOIN road_reports report
      ON report.road_segment_id = road.segment_id AND report.status = 'ready'
    JOIN road_assessments assessment ON assessment.report_id = report.id
    WHERE road.geom && ST_MakeEnvelope(:min_lng, :min_lat, :max_lng, :max_lat, 4326)
    GROUP BY road.segment_id, road.geom
    ORDER BY MAX(report.created_at) DESC
    LIMIT :limit
''')


def cache_key(request: RouteRequest, version: int) -> str:
    payload = {
        "o": [round(request.origin.latitude, 5), round(request.origin.longitude, 5)],
        "d": [round(request.destination.latitude, 5), round(request.destination.longitude, 5)],
        "v": version,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]
    return f"pathfinder:routes:{digest}"


def _distance_meters(start: tuple[float, float], end: tuple[float, float]) -> float:
    latitude_scale = 111_320
    mean_latitude = math.radians((start[0] + end[0]) / 2)
    longitude_scale = latitude_scale * math.cos(mean_latitude)
    return math.hypot(
        (end[0] - start[0]) * latitude_scale,
        (end[1] - start[1]) * longitude_scale,
    )


def _route_pieces(encoded: str, target_meters: float = 45) -> list[dict]:
    points = polyline.decode(encoded)
    pieces: list[dict] = []
    ordinal = 0
    for start, end in zip(points, points[1:], strict=False):
        subdivisions = max(1, math.ceil(_distance_meters(start, end) / target_meters))
        for index in range(subdivisions):
            ratio_start = index / subdivisions
            ratio_end = (index + 1) / subdivisions
            first = (
                start[0] + (end[0] - start[0]) * ratio_start,
                start[1] + (end[1] - start[1]) * ratio_start,
            )
            second = (
                start[0] + (end[0] - start[0]) * ratio_end,
                start[1] + (end[1] - start[1]) * ratio_end,
            )
            route_points = [first, second]
            wkt = f"SRID=4326;LINESTRING({first[1]} {first[0]},{second[1]} {second[0]})"
            canonical = sorted(
                (f"{first[0]:.6f},{first[1]:.6f}", f"{second[0]:.6f},{second[1]:.6f}")
            )
            pieces.append(
                {
                    "ordinal": ordinal,
                    "points": route_points,
                    "wkt": wkt,
                    "encoded_polyline": polyline.encode(route_points, 5),
                    "segment_hash": hashlib.sha256("|".join(canonical).encode()).hexdigest(),
                }
            )
            ordinal += 1
    return pieces


def _quality_band(quality: float | None) -> str:
    if quality is None:
        return "unknown"
    if quality < 30:
        return "critical"
    if quality < 50:
        return "poor"
    if quality < 70:
        return "fair"
    if quality < 85:
        return "good"
    return "excellent"


def _merge_segments(pieces: list[dict], score_rows: list) -> list[RoadQualitySegment]:
    rows = {int(row.ordinal): row for row in score_rows}
    merged: list[dict] = []
    for piece in pieces:
        row = rows.get(piece["ordinal"])
        count = int(row.observation_count or 0) if row else 0
        quality = float(row.road_quality) if row and row.road_quality is not None else None
        confidence = float(row.confidence) if row and row.confidence is not None else 0.0
        band = _quality_band(quality)
        if merged and merged[-1]["band"] == band:
            merged[-1]["points"].append(piece["points"][-1])
            merged[-1]["weighted_quality"] += (quality or 0) * max(count, 1)
            merged[-1]["weighted_confidence"] += confidence * max(count, 1)
            merged[-1]["weight"] += max(count, 1)
            merged[-1]["observation_count"] += count
            continue
        merged.append(
            {
                "band": band,
                "points": list(piece["points"]),
                "weighted_quality": (quality or 0) * max(count, 1),
                "weighted_confidence": confidence * max(count, 1),
                "weight": max(count, 1),
                "observation_count": count,
            }
        )
    return [
        RoadQualitySegment(
            encoded_polyline=polyline.encode(item["points"], 5),
            road_quality=(
                round(item["weighted_quality"] / item["weight"], 1)
                if item["band"] != "unknown"
                else None
            ),
            observation_count=item["observation_count"],
            confidence=round(item["weighted_confidence"] / item["weight"], 3),
            status="observed" if item["band"] != "unknown" else "unknown",
        )
        for item in merged
    ]


def _score_candidate(db: Session, candidate: CandidateRoute) -> tuple[list[RoadQualitySegment], float, float]:
    pieces = _route_pieces(candidate.encoded_polyline)
    if not pieces:
        return [], 50.0, 0.0
    payload = json.dumps([{"ordinal": item["ordinal"], "wkt": item["wkt"]} for item in pieces])
    radius = get_settings().route_quality_radius_meters
    # Try OSM-based scoring; fall back to proximity-based scoring
    rows = db.execute(
        OSM_SEGMENT_QUALITY_SQL,
        {"segments": payload, "radius": radius},
    ).all()
    has_osm_data = any(int(row.observation_count or 0) > 0 for row in rows)
    if not has_osm_data:
        rows = db.execute(
            SEGMENT_QUALITY_SQL,
            {"segments": payload, "radius": radius},
        ).all()
    quality_segments = _merge_segments(pieces, rows)
    observed = [segment for segment in quality_segments if segment.status == "observed"]
    observed_piece_count = sum(1 for row in rows if int(row.observation_count or 0) > 0)
    coverage = observed_piece_count / len(pieces)
    quality = (
        sum((segment.road_quality or 0) * max(segment.observation_count, 1) for segment in observed)
        / sum(max(segment.observation_count, 1) for segment in observed)
        if observed
        else 50.0
    )
    db.execute(
        STORE_SEGMENTS_SQL,
        {
            "segments": json.dumps(
                [
                    {
                        "segment_hash": item["segment_hash"],
                        "encoded_polyline": item["encoded_polyline"],
                        "wkt": item["wkt"],
                    }
                    for item in pieces
                ]
            )
        },
    )
    return quality_segments, quality, coverage


def score_candidates(
    candidates: list[CandidateRoute],
    analyses: list[tuple[list[RoadQualitySegment], float, float]],
) -> list[RouteOption]:
    if not candidates:
        return []
    min_distance = min(route.distance_meters for route in candidates)
    min_duration = min(route.duration_seconds for route in candidates)
    options = []
    for index, (route, (segments, observed, coverage)) in enumerate(
        zip(candidates, analyses, strict=True)
    ):
        coverage = max(0.0, min(1.0, coverage))
        effective_quality = 50 + coverage * (observed - 50)
        distance_score = min_distance / max(route.distance_meters, 1) * 100
        duration_score = min_duration / max(route.duration_seconds, 1) * 100
        final = 0.25 * distance_score + 0.35 * duration_score + 0.40 * effective_quality
        options.append(
            RouteOption(
                id=f"route-{index + 1}",
                summary=route.summary,
                encoded_polyline=route.encoded_polyline,
                distance_meters=route.distance_meters,
                duration_seconds=route.duration_seconds,
                road_quality=round(effective_quality, 1),
                quality_coverage=round(coverage, 3),
                pathfinder_score=round(final, 1),
                quality_segments=segments,
            )
        )
    options.sort(key=lambda item: item.pathfinder_score, reverse=True)
    options[0].is_recommended = True
    return options


def route_wkt(encoded: str) -> str:
    coordinates = polyline.decode(encoded)
    points = ",".join(f"{longitude} {latitude}" for latitude, longitude in coordinates)
    return f"SRID=4326;LINESTRING({points})"


def nearby_quality_segments(
    db: Session,
    min_lat: float,
    min_lng: float,
    max_lat: float,
    max_lng: float,
    zoom: int,
) -> list[RoadQualitySegment]:
    limit = 1200 if zoom >= 15 else 700 if zoom >= 13 else 350
    params = {
        "min_lat": min_lat,
        "min_lng": min_lng,
        "max_lat": max_lat,
        "max_lng": max_lng,
        "radius": get_settings().route_quality_radius_meters,
        "limit": limit,
    }
    # Try OSM-based segments first; fall back to route-derived segments
    rows = db.execute(OSM_NEARBY_SEGMENTS_SQL, params).all()
    if not rows:
        rows = db.execute(NEARBY_SEGMENTS_SQL, params).all()
    return [
        RoadQualitySegment(
            encoded_polyline=row.encoded_polyline,
            road_quality=round(float(row.road_quality), 1),
            observation_count=int(row.observation_count),
            confidence=round(float(row.confidence or 0), 3),
            status="observed",
        )
        for row in rows
    ]


async def recommend_routes(request: RouteRequest, db: Session) -> RouteResponse:
    version = cache.data_version()
    key = cache_key(request, version)
    cached = cache.get_json(key)
    if cached:
        cached["cache_status"] = "hit"
        return RouteResponse.model_validate(cached)
    candidates = await routing_provider.routes(request.origin, request.destination)
    analyses: list[tuple[list[RoadQualitySegment], float, float]] = []
    database_available = True
    for candidate in candidates:
        if not database_available:
            analyses.append(([], 50.0, 0.0))
            continue
        try:
            analyses.append(_score_candidate(db, candidate))
        except Exception:
            db.rollback()
            analyses.append(([], 50.0, 0.0))
            database_available = False
    if database_available:
        db.commit()
    response = RouteResponse(
        routes=score_candidates(candidates, analyses),
        cache_status="miss",
        road_data_version=version,
    )
    cache.set_json(key, response.model_dump(), get_settings().route_cache_ttl_seconds)
    return response
