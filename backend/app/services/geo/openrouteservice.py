import httpx

from ...config import get_settings
from ...schemas import Coordinate
from .types import CandidateRoute, PlaceSuggestion


class OpenRouteServiceProvider:
    name = 'openrouteservice'

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.routing_base_url.rstrip('/')
        self.geocoding_url = settings.geocoding_base_url.rstrip('/')
        self.api_key = settings.ors_api_key

    @property
    def headers(self) -> dict[str, str]:
        return {'Authorization': self.api_key} if self.api_key else {}

    async def routes(self, origin: Coordinate, destination: Coordinate) -> list[CandidateRoute]:
        body = {
            'coordinates': [
                [origin.longitude, origin.latitude],
                [destination.longitude, destination.latitude],
            ],
            'instructions': False,
            'alternative_routes': {'target_count': 3, 'share_factor': 0.8},
        }
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f'{self.base_url}/v2/directions/driving-car',
                json=body,
                headers=self.headers,
            )
            response.raise_for_status()
        candidates = []
        for index, route in enumerate(response.json().get('routes', [])[:3]):
            summary = route.get('summary', {})
            candidates.append(CandidateRoute(
                summary=f'Route {index + 1}',
                encoded_polyline=route['geometry'],
                distance_meters=round(float(summary['distance'])),
                duration_seconds=round(float(summary['duration'])),
                provider=self.name,
            ))
        return candidates

    async def autocomplete(self, query: str, session_token: str | None = None) -> list[PlaceSuggestion]:
        params = {
            'text': query,
            'boundary.country': 'IN',
            'focus.point.lat': 12.9716,
            'focus.point.lon': 77.5946,
            'size': 5,
        }
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(
                f'{self.geocoding_url}/geocode/autocomplete', params=params, headers=self.headers
            )
            response.raise_for_status()
        return self._places(response.json())

    async def geocode(self, query: str) -> dict | None:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(
                f'{self.geocoding_url}/geocode/search',
                params={'text': query, 'boundary.country': 'IN', 'size': 1},
                headers=self.headers,
            )
            response.raise_for_status()
        places = self._places(response.json())
        return places[0].as_dict() if places else None

    @staticmethod
    def _places(payload: dict) -> list[PlaceSuggestion]:
        results = []
        for feature in payload.get('features', []):
            coordinates = feature.get('geometry', {}).get('coordinates', [])
            properties = feature.get('properties', {})
            if len(coordinates) < 2:
                continue
            provider_id = properties.get('gid') or properties.get('id')
            results.append(PlaceSuggestion(
                place_id=f'pelias:{provider_id}',
                label=properties.get('label') or properties.get('name') or 'Unnamed place',
                latitude=float(coordinates[1]),
                longitude=float(coordinates[0]),
            ))
        return results
