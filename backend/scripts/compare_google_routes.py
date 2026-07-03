'''Transient ORS versus Google research benchmark.

No provider geometry or response body is persisted. Google output is used only
to calculate aggregate distance, duration, latency, and success metrics.
'''

import asyncio
import time

from app.config import get_settings
from app.schemas import Coordinate
from app.services.geo.openrouteservice import OpenRouteServiceProvider
from app.services.google_maps import maps_client


PAIRS = [
    (Coordinate(latitude=12.9763, longitude=77.5929), Coordinate(latitude=12.9784, longitude=77.6408)),
    (Coordinate(latitude=12.9352, longitude=77.6245), Coordinate(latitude=12.9767, longitude=77.5713)),
]


async def main() -> None:
    settings = get_settings()
    if not settings.google_research_enabled or not settings.google_maps_server_api_key:
        raise SystemExit('Set GOOGLE_RESEARCH_ENABLED=true and a server API key explicitly')
    ors = OpenRouteServiceProvider()
    for origin, destination in PAIRS:
        started = time.perf_counter()
        open_routes = await ors.routes(origin, destination)
        ors_ms = (time.perf_counter() - started) * 1000
        started = time.perf_counter()
        google_routes = await maps_client.routes(origin, destination)
        google_ms = (time.perf_counter() - started) * 1000
        if not open_routes or not google_routes:
            print({'ors_ok': bool(open_routes), 'google_ok': bool(google_routes)})
            continue
        print({
            'ors_ms': round(ors_ms, 1),
            'google_ms': round(google_ms, 1),
            'distance_delta_m': open_routes[0].distance_meters - google_routes[0].distance_meters,
            'duration_delta_s': open_routes[0].duration_seconds - google_routes[0].duration_seconds,
        })


if __name__ == '__main__':
    asyncio.run(main())
