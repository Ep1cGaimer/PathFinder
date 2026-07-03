import httpx

from ...config import get_settings
from .types import PlaceSuggestion


class PhotonGeocoder:
    name = 'photon'

    def __init__(self) -> None:
        self.base_url = get_settings().photon_base_url.rstrip('/')

    async def autocomplete(self, query: str, session_token: str | None = None) -> list[PlaceSuggestion]:
        headers = {'User-Agent': 'Pathfinder/1.0 (https://github.com/Ep1cGaimer/PathFinder)'}
        async with httpx.AsyncClient(timeout=8, headers=headers) as client:
            response = await client.get(f'{self.base_url}/api', params={
                'q': query, 'limit': 5, 'lat': 12.9716, 'lon': 77.5946, 'lang': 'en'
            })
            response.raise_for_status()
        return self._places(response.json())

    async def geocode(self, query: str) -> dict | None:
        places = await self.autocomplete(query)
        return places[0].as_dict() if places else None

    @staticmethod
    def _places(payload: dict) -> list[PlaceSuggestion]:
        results = []
        for feature in payload.get('features', []):
            coordinates = feature.get('geometry', {}).get('coordinates', [])
            properties = feature.get('properties', {})
            if len(coordinates) < 2:
                continue
            osm_type = properties.get('osm_type', 'X')
            osm_id = properties.get('osm_id', 'unknown')
            parts = [properties.get('name'), properties.get('district') or properties.get('city'), properties.get('state')]
            results.append(PlaceSuggestion(
                place_id=f'osm:{osm_type}:{osm_id}',
                label=', '.join(dict.fromkeys(part for part in parts if part)),
                latitude=float(coordinates[1]),
                longitude=float(coordinates[0]),
            ))
        return results
