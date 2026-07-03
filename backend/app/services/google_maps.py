from dataclasses import dataclass

import httpx
import polyline

from ..config import get_settings
from ..schemas import Coordinate


@dataclass
class CandidateRoute:
    summary: str
    encoded_polyline: str
    distance_meters: int
    duration_seconds: int


class GoogleMapsClient:
    routes_url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    autocomplete_url = "https://places.googleapis.com/v1/places:autocomplete"

    def __init__(self) -> None:
        self.api_key = get_settings().google_maps_server_api_key

    async def routes(self, origin: Coordinate, destination: Coordinate) -> list[CandidateRoute]:
        if not self.api_key:
            return self._demo_routes(origin, destination)
        body = {
            "origin": {"location": {"latLng": self._lat_lng(origin)}},
            "destination": {"location": {"latLng": self._lat_lng(destination)}},
            "travelMode": "DRIVE",
            "routingPreference": "TRAFFIC_AWARE",
            "computeAlternativeRoutes": True,
            "languageCode": "en-IN",
            "units": "METRIC",
        }
        headers = {
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": (
                "routes.distanceMeters,routes.duration,routes.polyline.encodedPolyline,"
                "routes.description,routes.routeLabels"
            ),
        }
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post(self.routes_url, json=body, headers=headers)
            response.raise_for_status()
        candidates = []
        for index, route in enumerate(response.json().get("routes", [])[:3]):
            duration = route.get("duration", "0s").rstrip("s")
            candidates.append(
                CandidateRoute(
                    summary=route.get("description") or f"Route {index + 1}",
                    encoded_polyline=route["polyline"]["encodedPolyline"],
                    distance_meters=int(route["distanceMeters"]),
                    duration_seconds=round(float(duration)),
                )
            )
        return candidates

    async def autocomplete(self, query: str, session_token: str | None) -> list[dict]:
        if not self.api_key:
            return [
                {
                    "place_id": "demo-indiranagar",
                    "label": "Indiranagar, Bengaluru",
                    "latitude": 12.9784,
                    "longitude": 77.6408,
                }
            ]
        body = {"input": query, "includedRegionCodes": ["in"]}
        if session_token:
            body["sessionToken"] = session_token
        headers = {
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "suggestions.placePrediction.placeId,suggestions.placePrediction.text",
        }
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.post(self.autocomplete_url, json=body, headers=headers)
            response.raise_for_status()
        return [
            {
                "place_id": item["placePrediction"]["placeId"],
                "label": item["placePrediction"]["text"]["text"],
            }
            for item in response.json().get("suggestions", [])
            if "placePrediction" in item
        ]

    async def geocode(self, query: str) -> dict | None:
        if not self.api_key:
            demos = {
                "cubbon park": {"label": "Cubbon Park, Bengaluru", "latitude": 12.9763, "longitude": 77.5929},
                "indiranagar": {"label": "Indiranagar, Bengaluru", "latitude": 12.9784, "longitude": 77.6408},
                "koramangala": {"label": "Koramangala, Bengaluru", "latitude": 12.9352, "longitude": 77.6245},
                "majestic": {"label": "Majestic, Bengaluru", "latitude": 12.9767, "longitude": 77.5713},
            }
            lowered = query.lower()
            return next((value for name, value in demos.items() if name in lowered), None)
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": query, "region": "in", "key": self.api_key},
            )
            response.raise_for_status()
        results = response.json().get("results", [])
        if not results:
            return None
        first = results[0]
        location = first["geometry"]["location"]
        return {"label": first["formatted_address"], "place_id": first["place_id"], "latitude": location["lat"], "longitude": location["lng"]}
    @staticmethod
    def _lat_lng(point: Coordinate) -> dict:
        return {"latitude": point.latitude, "longitude": point.longitude}

    @staticmethod
    def _demo_routes(origin: Coordinate, destination: Coordinate) -> list[CandidateRoute]:
        o = (origin.latitude, origin.longitude)
        d = (destination.latitude, destination.longitude)
        mid = ((o[0] + d[0]) / 2, (o[1] + d[1]) / 2)
        variants = [
            [o, mid, d],
            [o, (mid[0] + 0.006, mid[1] - 0.004), d],
            [o, (mid[0] - 0.004, mid[1] + 0.006), d],
        ]
        base = max(1200, int((((o[0] - d[0]) ** 2 + (o[1] - d[1]) ** 2) ** 0.5) * 111000))
        return [
            CandidateRoute(f"Demo route {i + 1}", polyline.encode(points, 5), int(base * factor), int(base * factor / 8.5))
            for i, (points, factor) in enumerate(zip(variants, (1.0, 1.13, 1.2), strict=True))
        ]


maps_client = GoogleMapsClient()
