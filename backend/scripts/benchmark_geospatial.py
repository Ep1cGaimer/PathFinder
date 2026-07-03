import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.database import SessionLocal
from app.services.routing import QUALITY_SQL

ROUTE = "SRID=4326;LINESTRING(77.5929 12.9763,77.6110 12.9791,77.6408 12.9784)"


def percentile(values: list[float], percent: float) -> float:
    return sorted(values)[min(len(values) - 1, round((len(values) - 1) * percent))]


def main(iterations: int = 100) -> None:
    durations = []
    with SessionLocal() as db:
        for _ in range(5):
            db.execute(QUALITY_SQL, {"route_wkt": ROUTE, "radius": get_settings().route_quality_radius_meters}).one()
        for _ in range(iterations):
            started = time.perf_counter()
            db.execute(QUALITY_SQL, {"route_wkt": ROUTE, "radius": get_settings().route_quality_radius_meters}).one()
            durations.append((time.perf_counter() - started) * 1000)
    print(f"iterations={iterations} p50={statistics.median(durations):.2f}ms p95={percentile(durations, .95):.2f}ms p99={percentile(durations, .99):.2f}ms")
    if percentile(durations, .95) >= 200:
        raise SystemExit("p95 exceeds the 200 ms resume threshold")


if __name__ == "__main__":
    main()
