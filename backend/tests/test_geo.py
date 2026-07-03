import pytest
import httpx
import asyncio
from unittest.mock import AsyncMock, patch
from app.schemas import Coordinate
from app.services.geo.openrouteservice import OpenRouteServiceProvider
from app.services.geo.photon import PhotonGeocoder
from app.services.geo.demo import DemoGeoProvider

def test_demo_geo_provider() -> None:
    provider = DemoGeoProvider()
    origin = Coordinate(latitude=12.9763, longitude=77.5929)
    dest = Coordinate(latitude=12.9784, longitude=77.6408)
    
    routes = asyncio.run(provider.routes(origin, dest))
    assert len(routes) == 3
    assert all(r.provider == "demo" for r in routes)
    assert all(r.encoded_polyline for r in routes)

    suggestions = asyncio.run(provider.autocomplete("cubbon"))
    assert len(suggestions) > 0
    assert any("Cubbon" in s.label for s in suggestions)

    geocode_res = asyncio.run(provider.geocode("cubbon park"))
    assert geocode_res is not None
    assert geocode_res["place_id"] == "demo-cubbon"


def test_ors_provider_routes_success() -> None:
    provider = OpenRouteServiceProvider()
    origin = Coordinate(latitude=12.9763, longitude=77.5929)
    dest = Coordinate(latitude=12.9784, longitude=77.6408)

    mock_response = {
        "routes": [
            {
                "summary": {"distance": 5200.5, "duration": 850.0},
                "geometry": "encoded_polyline_string"
            }
        ]
    }

    dummy_request = httpx.Request("POST", "https://api.openrouteservice.org/v2/directions/driving-car")
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = httpx.Response(200, json=mock_response, request=dummy_request)
        routes = asyncio.run(provider.routes(origin, dest))
        
        assert len(routes) == 1
        assert routes[0].distance_meters == 5200
        assert routes[0].duration_seconds == 850
        assert routes[0].encoded_polyline == "encoded_polyline_string"
        assert routes[0].provider == "openrouteservice"


def test_ors_provider_autocomplete_success() -> None:
    provider = OpenRouteServiceProvider()
    
    mock_response = {
        "features": [
            {
                "geometry": {"coordinates": [77.5929, 12.9763]},
                "properties": {"gid": "pelias:1", "label": "Cubbon Park"}
            }
        ]
    }

    dummy_request = httpx.Request("GET", "https://api.openrouteservice.org/geocode/autocomplete")
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = httpx.Response(200, json=mock_response, request=dummy_request)
        suggestions = asyncio.run(provider.autocomplete("cubbon"))
        
        assert len(suggestions) == 1
        assert suggestions[0].place_id == "pelias:pelias:1"
        assert suggestions[0].label == "Cubbon Park"
        assert suggestions[0].latitude == 12.9763
        assert suggestions[0].longitude == 77.5929


def test_photon_provider_autocomplete_success() -> None:
    provider = PhotonGeocoder()

    mock_response = {
        "features": [
            {
                "geometry": {"coordinates": [77.6408, 12.9784]},
                "properties": {
                    "osm_type": "W",
                    "osm_id": 12345,
                    "name": "Indiranagar",
                    "city": "Bengaluru",
                    "state": "Karnataka"
                }
            }
        ]
    }

    dummy_request = httpx.Request("GET", "http://localhost:2322/api")
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = httpx.Response(200, json=mock_response, request=dummy_request)
        suggestions = asyncio.run(provider.autocomplete("indiranagar"))
        
        assert len(suggestions) == 1
        assert suggestions[0].place_id == "osm:W:12345"
        assert "Indiranagar" in suggestions[0].label
        assert suggestions[0].latitude == 12.9784
        assert suggestions[0].longitude == 77.6408


def test_ors_provider_failure_raises() -> None:
    provider = OpenRouteServiceProvider()
    origin = Coordinate(latitude=12.9763, longitude=77.5929)
    dest = Coordinate(latitude=12.9784, longitude=77.6408)

    dummy_request = httpx.Request("POST", "https://api.openrouteservice.org/v2/directions/driving-car")
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.side_effect = httpx.HTTPStatusError("API Error", request=dummy_request, response=httpx.Response(500, request=dummy_request))
        
        with pytest.raises(httpx.HTTPError):
            asyncio.run(provider.routes(origin, dest))
