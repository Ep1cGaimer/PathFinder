export type Coordinate = {
  latitude: number;
  longitude: number;
  label: string;
  place_id?: string;
};

export type PlaceSuggestion = { place_id: string; label: string };

export type RoadQualitySegment = {
  encoded_polyline: string;
  road_quality: number | null;
  observation_count: number;
  confidence: number;
  status: "observed" | "unknown";
};

export type RouteOption = {
  id: string;
  summary: string;
  encoded_polyline: string;
  distance_meters: number;
  duration_seconds: number;
  road_quality: number;
  quality_coverage: number;
  pathfinder_score: number;
  quality_segments: RoadQualitySegment[];
  is_recommended: boolean;
};

export type RouteResponse = {
  routes: RouteOption[];
  cache_status: string;
  road_data_version: number;
};

export type MapBounds = {
  min_lat: number;
  min_lng: number;
  max_lat: number;
  max_lng: number;
  zoom: number;
};

export type Assessment = {
  model_version: string;
  detections: { damage_class: string; confidence: number }[];
  surface_damage: number;
  traffic_safety_risk: number;
  ride_discomfort: number;
  waterlogging: number;
  urgency_for_repair: number;
  road_quality: number;
  confidence: number;
};

export type RoadReport = {
  id: string;
  latitude: number;
  longitude: number;
  description: string;
  status: string;
  is_demo: boolean;
  created_at: string;
  image_url?: string;
  assessment?: Assessment;
  road_place_id?: string;
  snap_status?: string;
  snapped_location?: { latitude: number; longitude: number };
};
