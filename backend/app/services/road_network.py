from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session


SNAP_SQL = text('''
    WITH point AS (
      SELECT ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326) AS geom
    )
    SELECT road.segment_id,
      road.osm_way_id,
      ST_Y(ST_ClosestPoint(road.geom, point.geom)) AS latitude,
      ST_X(ST_ClosestPoint(road.geom, point.geom)) AS longitude,
      ST_Distance(road.geom::geography, point.geom::geography) AS distance_meters
    FROM osm_road_segments road, point
    WHERE ST_DWithin(road.geom::geography, point.geom::geography, :max_distance)
    ORDER BY road.geom <-> point.geom
    LIMIT 1
''')


@dataclass(frozen=True)
class SnappedRoad:
    segment_id: str
    osm_way_id: int
    latitude: float
    longitude: float
    distance_meters: float


def snap_to_road(
    db: Session, latitude: float, longitude: float, max_distance: float = 30
) -> SnappedRoad | None:
    try:
        row = db.execute(SNAP_SQL, {
            'latitude': latitude,
            'longitude': longitude,
            'max_distance': max_distance,
        }).one_or_none()
    except Exception:
        db.rollback()
        return None
    if row is None:
        return None
    return SnappedRoad(
        segment_id=row.segment_id,
        osm_way_id=int(row.osm_way_id),
        latitude=float(row.latitude),
        longitude=float(row.longitude),
        distance_meters=float(row.distance_meters),
    )
