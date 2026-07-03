import json
import statistics
import sys
import time
from pathlib import Path

import polyline

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.database import SessionLocal
from app.services.routing import SEGMENT_QUALITY_SQL, _route_pieces

ROUTE = polyline.encode(
    [(12.9763, 77.5929), (12.95575, 77.6087), (12.9352, 77.6245)],
    5,
)


def percentile(values: list[float], percent: float) -> float:
    return sorted(values)[min(len(values) - 1, round((len(values) - 1) * percent))]


def main(iterations: int = 100) -> None:
    pieces = _route_pieces(ROUTE)
    payload = json.dumps(
        [{"ordinal": piece["ordinal"], "wkt": piece["wkt"]} for piece in pieces]
    )
    parameters = {
        "segments": payload,
        "radius": get_settings().route_quality_radius_meters,
    }
    durations = []
    with SessionLocal() as db:
        for _ in range(5):
            db.execute(SEGMENT_QUALITY_SQL, parameters).all()
        for _ in range(iterations):
            started = time.perf_counter()
            db.execute(SEGMENT_QUALITY_SQL, parameters).all()
            durations.append((time.perf_counter() - started) * 1000)
    print(
        f"segments={len(pieces)} iterations={iterations} "
        f"p50={statistics.median(durations):.2f}ms "
        f"p95={percentile(durations, .95):.2f}ms "
        f"p99={percentile(durations, .99):.2f}ms"
    )
    if percentile(durations, .95) >= 200:
        raise SystemExit("p95 exceeds the 200 ms resume threshold")


if __name__ == "__main__":
    main()