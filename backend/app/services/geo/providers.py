from ...config import get_settings
from .base import GeocodingProvider, RoutingProvider
from .demo import DemoGeoProvider
from .openrouteservice import OpenRouteServiceProvider
from .osrm import OSRMProvider
from .photon import PhotonGeocoder


def _routing() -> RoutingProvider:
    provider = get_settings().routing_provider.casefold()
    if provider == 'demo':
        return DemoGeoProvider()
    if provider == 'ors':
        return OpenRouteServiceProvider()
    if provider == 'osrm':
        return OSRMProvider()
    raise RuntimeError(f'Unsupported routing provider: {provider}')


def _geocoding() -> GeocodingProvider:
    provider = get_settings().geocoding_provider.casefold()
    if provider == 'demo':
        return DemoGeoProvider()
    if provider == 'ors':
        return OpenRouteServiceProvider()
    if provider == 'photon':
        return PhotonGeocoder()
    raise RuntimeError(f'Unsupported geocoding provider: {provider}')


routing_provider = _routing()
geocoder = _geocoding()

