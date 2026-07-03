from pathlib import Path

from ..config import get_settings


class ImageStorage:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.local_root = Path(__file__).resolve().parents[2] / 'uploads'

    def _client(self):
        import boto3
        return boto3.client(
            's3',
            endpoint_url=self.settings.s3_endpoint_url,
            region_name=self.settings.s3_region,
            aws_access_key_id=self.settings.s3_access_key_id,
            aws_secret_access_key=self.settings.s3_secret_access_key,
        )

    def put(self, key: str, contents: bytes, content_type: str) -> None:
        if not self.settings.s3_endpoint_url:
            path = self.local_root / key
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
            return
        self._client().put_object(
            Bucket=self.settings.s3_bucket,
            Key=key,
            Body=contents,
            ContentType=content_type,
            CacheControl='public, max-age=3600',
        )

    def get(self, key: str) -> bytes:
        if not self.settings.s3_endpoint_url:
            return (self.local_root / key).read_bytes()
        return self._client().get_object(Bucket=self.settings.s3_bucket, Key=key)['Body'].read()


image_storage = ImageStorage()
