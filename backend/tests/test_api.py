from fastapi.testclient import TestClient

from app.main import app

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


def test_geocoding_returns_real_results() -> None:
    response = client.get("/api/v1/places/geocode", params={"q": "Koramangala"})

    assert response.status_code == 200
    assert "Koramangala" in response.json()["label"]
