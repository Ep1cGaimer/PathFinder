from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateRoute:
    summary: str
    encoded_polyline: str
    distance_meters: int
    duration_seconds: int
    provider: str = 'unknown'


@dataclass(frozen=True)
class PlaceSuggestion:
    place_id: str
    label: str
    latitude: float | None = None
    longitude: float | None = None

    def as_dict(self) -> dict:
        value = {'place_id': self.place_id, 'label': self.label}
        if self.latitude is not None and self.longitude is not None:
            value.update(latitude=self.latitude, longitude=self.longitude)
        return value
