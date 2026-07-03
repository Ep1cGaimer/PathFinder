TRUNCATE osm_road_segments;

WITH densified AS (
  SELECT osm_way_id, name, highway, surface,
    ST_Segmentize(geom::geography, 50)::geometry AS geom
  FROM osm_roads_raw
  WHERE ST_NPoints(geom) >= 2
), segments AS (
  SELECT osm_way_id, name, highway, surface,
    (dumped).path[1] - 1 AS segment_index,
    (dumped).geom::geometry(LineString, 4326) AS geom
  FROM (
    SELECT osm_way_id, name, highway, surface, ST_DumpSegments(geom) AS dumped
    FROM densified
  ) value
)
INSERT INTO osm_road_segments (
  segment_id, osm_way_id, segment_index, name, highway, surface, geom
)
SELECT osm_way_id || ':' || segment_index,
  osm_way_id, segment_index, name, highway, surface, geom
FROM segments
ON CONFLICT (segment_id) DO UPDATE SET
  name = EXCLUDED.name,
  highway = EXCLUDED.highway,
  surface = EXCLUDED.surface,
  geom = EXCLUDED.geom,
  source_updated_at = now();

ANALYZE osm_road_segments;
