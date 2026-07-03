import json
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from ..config import get_settings


class Cache:
    def __init__(self) -> None:
        self.client = Redis.from_url(get_settings().cache_url, decode_responses=True, socket_connect_timeout=0.5)

    def ping(self) -> bool:
        try:
            return bool(self.client.ping())
        except RedisError:
            return False

    def get_json(self, key: str) -> dict[str, Any] | None:
        try:
            value = self.client.get(key)
            return json.loads(value) if value else None
        except (RedisError, json.JSONDecodeError):
            return None

    def set_json(self, key: str, value: dict[str, Any], ttl: int) -> None:
        try:
            self.client.setex(key, ttl, json.dumps(value))
        except RedisError:
            pass

    def data_version(self) -> int:
        try:
            return int(self.client.get("pathfinder:road-data-version") or 1)
        except (RedisError, ValueError):
            return 1

    def bump_data_version(self) -> None:
        try:
            self.client.incr("pathfinder:road-data-version")
        except RedisError:
            pass

    def allow(self, bucket: str, limit: int, window_seconds: int) -> bool:
        try:
            key = f"pathfinder:rate:{bucket}"
            count = self.client.incr(key)
            if count == 1:
                self.client.expire(key, window_seconds)
            return count <= limit
        except RedisError:
            return True


cache = Cache()
