import httpx

from ...schemas import Coordinate
from .types import CandidateRoute


class OSRMProvider:
    """Keyless routing via the public OSRM demo server.

    Uses real OpenStreetMap road data — routes follow actual roads,
    not straight lines. Rate-limited to ~1 req/s by the public server.
    """

    name = 'osrm'

    def __init__(self, base_url: str = 'https://router.project-osrm.org') -> None:
        self.base_url = base_url.rstrip('/')

    async def routes(
        self, origin: Coordinate, destination: Coordinate
    ) -> list[CandidateRoute]:
        coordinates = f'{origin.longitude},{origin.latitude};{destination.longitude},{destination.latitude}'
        url = f'{self.base_url}/route/v1/driving/{coordinates}'
        params = {
            'alternatives': 'true',
            'overview': 'full',
            'geometries': 'polyline',
            'steps': 'false',
        }
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

        data = response.json()
        if data.get('code') != 'Ok':
            raise RuntimeError(f'OSRM error: {data.get("code")} — {data.get("message", "")}')

        candidates = []
        for index, route in enumerate(data.get('routes', [])[:3]):
            candidates.append(CandidateRoute(
                summary=f'Route {index + 1}',
                encoded_polyline=route['geometry'],
                distance_meters=round(float(route['distance'])),
                duration_seconds=round(float(route['duration'])),
                provider=self.name,
            ))
        return candidates
