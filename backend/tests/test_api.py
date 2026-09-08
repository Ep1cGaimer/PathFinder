from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.main import app
from app.routers import places

client = TestClient(app)


def test_openapi_and_health_are_available_without_authentication() -> None:
    assert client.get("/openapi.json").status_code == 200
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] in {"ok", "degraded"}
    assert "X-Request-ID" in response.headers


def test_route_request_validates_distinct_points() -> None:
    response = client.post(
        "/api/v1/routes/recommend",
        json={
            "origin": {"latitude": 12.97, "longitude": 77.59},
            "destination": {"latitude": 12.97, "longitude": 77.59},
        },
    )
    assert response.status_code == 422


def test_geocoding_returns_provider_results(monkeypatch) -> None:
    monkeypatch.setattr(
        places.geocoder,
        'geocode',
        AsyncMock(return_value={
            'place_id': 'osm:R:123',
            'label': 'Koramangala, Bengaluru',
            'latitude': 12.9352,
            'longitude': 77.6245,
        }),
    )
    response = client.get("/api/v1/places/geocode", params={"q": "Koramangala"})

    assert response.status_code == 200
    assert "Koramangala" in response.json()["label"]


def test_report_rejects_out_of_bounds_coordinates() -> None:
    headers = {"Authorization": "Bearer dev-token"}
    response = client.post(
        "/api/v1/reports",
        data={"latitude": 120.0, "longitude": 77.59, "description": "bad lat"},
        files={"image": ("test.jpg", b"fake image bytes", "image/jpeg")},
        headers=headers,
    )
    assert response.status_code == 422
    assert "Invalid coordinates" in response.json()["detail"]


def test_report_rejects_invalid_image_content() -> None:
    headers = {"Authorization": "Bearer dev-token"}
    response = client.post(
        "/api/v1/reports",
        data={"latitude": 12.97, "longitude": 77.59, "description": "not an image"},
        files={"image": ("test.jpg", b"this is not real jpeg data", "image/jpeg")},
        headers=headers,
    )
    assert response.status_code == 422
    assert "not a valid image" in response.json()["detail"]

