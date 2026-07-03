import math

import polyline

from ...schemas import Coordinate
from .types import CandidateRoute, PlaceSuggestion


PLACES = {
    'cubbon park': ('demo-cubbon', 'Cubbon Park, Bengaluru', 12.9763, 77.5929),
    'indiranagar': ('demo-indiranagar', 'Indiranagar, Bengaluru', 12.9784, 77.6408),
    'koramangala': ('demo-koramangala', 'Koramangala, Bengaluru', 12.9352, 77.6245),
    'majestic': ('demo-majestic', 'Majestic, Bengaluru', 12.9767, 77.5713),
    'brigade road': ('demo-brigade', 'Brigade Road, Bengaluru', 12.9716, 77.6070),
}


class DemoGeoProvider:
    name = 'demo'

    async def routes(
        self, origin: Coordinate, destination: Coordinate
    ) -> list[CandidateRoute]:
        start = (origin.latitude, origin.longitude)
        end = (destination.latitude, destination.longitude)
        middle = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
        variants = [
            [start, middle, end],
            [start, (middle[0] + 0.006, middle[1] - 0.004), end],
            [start, (middle[0] - 0.004, middle[1] + 0.006), end],
        ]
        base = max(
            1200,
            round(math.hypot(start[0] - end[0], start[1] - end[1]) * 111_000),
        )
        return [
            CandidateRoute(
                summary=f'Demo route {index + 1}',
                encoded_polyline=polyline.encode(points, 5),
                distance_meters=round(base * factor),
                duration_seconds=round(base * factor / 8.5),
                provider=self.name,
            )
            for index, (points, factor) in enumerate(
                zip(variants, (1.0, 1.13, 1.2), strict=True)
            )
        ]

    async def autocomplete(
        self, query: str, session_token: str | None = None
    ) -> list[PlaceSuggestion]:
        lowered = query.casefold()
        return [
            PlaceSuggestion(*value)
            for name, value in PLACES.items()
            if lowered in name or lowered in value[1].casefold()
        ][:5]

    async def geocode(self, query: str) -> dict | None:
        lowered = query.casefold()
        match = next(
            (value for name, value in PLACES.items() if lowered in name or name in lowered),
            None,
        )
        if not match:
            return None
        place_id, label, latitude, longitude = match
        return {
            'place_id': place_id,
            'label': label,
            'latitude': latitude,
            'longitude': longitude,
        }
