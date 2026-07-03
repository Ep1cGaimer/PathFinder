from pathlib import Path

import httpx

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

    def put(self, key: str, contents: bytes, content_type: str, bearer_token: str = '') -> None:
        if self.settings.supabase_url and self.settings.supabase_publishable_key and bearer_token != 'dev-token':
            response = httpx.post(
                f'{self.settings.supabase_url.rstrip("/")}/storage/v1/object/{self.settings.s3_bucket}/{key}',
                content=contents,
                headers={
                    'apikey': self.settings.supabase_publishable_key,
                    'Authorization': f'Bearer {bearer_token}',
                    'Content-Type': content_type,
                    'Cache-Control': 'public, max-age=3600',
                    'x-upsert': 'false',
                },
                timeout=20,
            )
            response.raise_for_status()
            return
        if self.settings.s3_endpoint_url:
            self._client().put_object(
                Bucket=self.settings.s3_bucket,
                Key=key,
                Body=contents,
                ContentType=content_type,
                CacheControl='public, max-age=3600',
            )
            return
        path = self.local_root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)

    def get(self, key: str) -> bytes:
        if self.settings.supabase_url and self.settings.supabase_publishable_key:
            response = httpx.get(
                f'{self.settings.supabase_url.rstrip("/")}/storage/v1/object/public/{self.settings.s3_bucket}/{key}',
                headers={'apikey': self.settings.supabase_publishable_key},
                timeout=20,
            )
            response.raise_for_status()
            return response.content
        if self.settings.s3_endpoint_url:
            return self._client().get_object(Bucket=self.settings.s3_bucket, Key=key)['Body'].read()
        return (self.local_root / key).read_bytes()


image_storage = ImageStorage()
