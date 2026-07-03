import polyline

from app.schemas import Coordinate, RouteRequest
from app.services.google_maps import CandidateRoute
from app.services.routing import cache_key, score_candidates


def candidate(name: str, distance: int, duration: int) -> CandidateRoute:
    return CandidateRoute(name, polyline.encode([(12.97, 77.59), (12.98, 77.64)]), distance, duration)


def test_quality_can_outweigh_small_detour() -> None:
    routes = [candidate("fast rough", 5000, 900), candidate("smooth", 5300, 960)]
    result = score_candidates(routes, [([], 20, 1.0), ([], 90, 1.0)])
    assert result[0].summary == "smooth"
    assert result[0].is_recommended is True


def test_sparse_quality_is_shrunk_toward_neutral() -> None:
    routes = [candidate("route", 5000, 900)]
    result = score_candidates(routes, [([], 100, 0.1)])
    assert result[0].road_quality == 55.0


def test_zero_coverage_is_neutral() -> None:
    result = score_candidates([candidate("route", 5000, 900)], [([], 0, 0)])
    assert result[0].road_quality == 50.0


def test_cache_key_rounds_gps_noise_and_versions_data() -> None:
    first = RouteRequest(origin=Coordinate(latitude=12.970001, longitude=77.590001), destination=Coordinate(latitude=12.98, longitude=77.64))
    noisy = RouteRequest(origin=Coordinate(latitude=12.970002, longitude=77.590002), destination=Coordinate(latitude=12.98, longitude=77.64))
    assert cache_key(first, 1) == cache_key(noisy, 1)
    assert cache_key(first, 1) != cache_key(first, 2)
