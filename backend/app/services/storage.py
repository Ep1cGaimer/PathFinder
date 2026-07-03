from pathlib import Path

from ..config import get_settings


class ImageStorage:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.local_root = Path(__file__).resolve().parents[2] / "uploads"

    def put(self, key: str, contents: bytes, content_type: str) -> None:
        if not self.settings.google_cloud_storage_bucket:
            path = self.local_root / key
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
            return
        from google.cloud import storage
        storage.Client().bucket(self.settings.google_cloud_storage_bucket).blob(key).upload_from_string(contents, content_type=content_type)

    def get(self, key: str) -> bytes:
        if not self.settings.google_cloud_storage_bucket:
            return (self.local_root / key).read_bytes()
        from google.cloud import storage
        return storage.Client().bucket(self.settings.google_cloud_storage_bucket).blob(key).download_as_bytes()


image_storage = ImageStorage()
