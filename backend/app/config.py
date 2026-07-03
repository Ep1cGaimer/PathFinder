from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    valkey_url: str = ''
    routing_provider: str = 'osrm'
    geocoding_provider: str = 'photon'
    routing_base_url: str = 'https://api.openrouteservice.org'
    geocoding_base_url: str = 'https://api.openrouteservice.org'
    ors_api_key: str = ''
    photon_base_url: str = 'https://photon.komoot.io'
    map_region_bbox: str = '77.35,12.75,77.85,13.20'
    google_research_enabled: bool = False
    supabase_url: str = ''
    supabase_publishable_key: str = ''
    supabase_jwks_url: str = ''
    supabase_jwt_audience: str = 'authenticated'
    s3_endpoint_url: str = ''
    s3_region: str = 'auto'
    s3_bucket: str = 'road-reports'
    s3_access_key_id: str = ''
    s3_secret_access_key: str = ''

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    database_url: str = "postgresql+psycopg://pathfinder:pathfinder@localhost:5432/pathfinder"
    redis_url: str = "redis://localhost:6379/0"
    google_maps_server_api_key: str = ""
    allowed_origins: str = "http://localhost:8081,http://localhost:19006,http://127.0.0.1:4173"
    model_path: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2]
        / "trainedModels"
        / "ssd_mobilenet_innference_graph.pb"
    )
    route_cache_ttl_seconds: int = 300
    route_quality_radius_meters: int = 30

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def cache_url(self) -> str:
        return self.valkey_url or self.redis_url
    @property
    def sqlalchemy_database_url(self) -> str:
        """Use the installed psycopg v3 driver with provider-style Postgres URLs."""
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql+psycopg://", 1)
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
