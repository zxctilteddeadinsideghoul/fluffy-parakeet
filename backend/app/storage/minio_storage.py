"""MinIO (S3-compatible) photo storage with presigned public URLs."""

from __future__ import annotations

import mimetypes
from datetime import timedelta
from io import BytesIO
from urllib.parse import urlparse
from uuid import uuid4

from minio import Minio

from app.core.config import settings


class MinioPhotoStorage:
    """Stores photos in a MinIO bucket and hands out presigned GET URLs.

    Two clients: one talks to the internal endpoint (container name), the
    other signs URLs for the publicly reachable endpoint, so the browser can
    download the object without breaking the host-based signature.
    """

    def __init__(
        self,
        client: Minio | None = None,
        *,
        endpoint: str = "",
        access_key: str = "",
        secret_key: str = "",
        bucket: str = "",
        secure: bool = False,
        public_endpoint: str = "",
        url_expiry_seconds: int = 3600,
        presign_client: Minio | None = None,
    ) -> None:
        self._bucket = bucket or settings.minio_bucket
        self._url_expiry_seconds = url_expiry_seconds or settings.minio_url_expiry_seconds
        self._endpoint = endpoint or settings.minio_endpoint
        self._client = client or Minio(
            self._endpoint,
            access_key=access_key or settings.minio_access_key,
            secret_key=secret_key or settings.minio_secret_key,
            secure=secure or settings.minio_secure,
        )
        self._presign_client = presign_client or self._build_public_client(
            public_endpoint or settings.minio_public_endpoint,
            access_key,
            secret_key,
        )

    def _build_public_client(self, public_endpoint: str, access_key: str, secret_key: str) -> Minio:
        parsed = urlparse(public_endpoint)
        return Minio(
            parsed.netloc,
            access_key=access_key or settings.minio_access_key,
            secret_key=secret_key or settings.minio_secret_key,
            secure=parsed.scheme == "https",
            region=settings.minio_region,
        )

    def ensure_bucket(self) -> None:
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

    def save(self, user_id: str, ext: str, content: bytes) -> str:
        storage_key = f"{user_id}/{uuid4().hex}{ext}"
        content_type = mimetypes.guess_type(storage_key)[0] or "application/octet-stream"
        self._client.put_object(
            self._bucket,
            storage_key,
            BytesIO(content),
            length=len(content),
            content_type=content_type,
        )
        return storage_key

    def open(self, storage_key: str) -> bytes:
        response = self._client.get_object(self._bucket, storage_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def public_url(self, storage_key: str, photo_id: str) -> str:
        return self._presign_client.presigned_get_object(
            self._bucket,
            storage_key,
            expires=timedelta(seconds=self._url_expiry_seconds),
        )