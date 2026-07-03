from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    database_url: str = "postgresql+psycopg://pathfinder:pathfinder@localhost:5432/pathfinder"
    redis_url: str = "redis://localhost:6379/0"
    google_maps_server_api_key: str = ""
    google_cloud_storage_bucket: str = ""
    firebase_project_id: str = "pathfinder-b5c55"
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
