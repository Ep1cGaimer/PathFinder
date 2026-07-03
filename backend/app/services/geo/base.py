from typing import Protocol

from ...schemas import Coordinate
from .types import CandidateRoute, PlaceSuggestion


class RoutingProvider(Protocol):
    name: str

    async def routes(
        self, origin: Coordinate, destination: Coordinate
    ) -> list[CandidateRoute]: ...


class GeocodingProvider(Protocol):
    name: str

    async def autocomplete(
        self, query: str, session_token: str | None = None
    ) -> list[PlaceSuggestion]: ...

    async def geocode(self, query: str) -> dict | None: ...
