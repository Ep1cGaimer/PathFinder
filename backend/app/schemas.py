from pydantic import BaseModel, Field, model_validator


class Coordinate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    label: str = Field(default="", max_length=200)
    place_id: str | None = None


class RouteRequest(BaseModel):
    origin: Coordinate
    destination: Coordinate

    @model_validator(mode="after")
    def distinct_points(self):
        if (
            abs(self.origin.latitude - self.destination.latitude) < 0.00001
            and abs(self.origin.longitude - self.destination.longitude) < 0.00001
        ):
            raise ValueError("Origin and destination must be different")
        return self


class RouteOption(BaseModel):
    id: str
    summary: str
    encoded_polyline: str
    distance_meters: int
    duration_seconds: int
    road_quality: float
    quality_coverage: float
    pathfinder_score: float
    is_recommended: bool = False


class RouteResponse(BaseModel):
    routes: list[RouteOption]
    cache_status: str
    road_data_version: int


class Detection(BaseModel):
    damage_class: str
    confidence: float


class AssessmentResponse(BaseModel):
    model_version: str
    detections: list[Detection]
    surface_damage: float
    traffic_safety_risk: float
    ride_discomfort: float
    waterlogging: float
    urgency_for_repair: float
    road_quality: float
    confidence: float
