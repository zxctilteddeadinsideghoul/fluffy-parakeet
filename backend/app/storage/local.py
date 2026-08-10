"""Photo storage: saves uploads and serves them back to callers.

A real object store with presigned URLs will replace this local implementation.
Until then, files live under the media root and are served by /media/{photoId}.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from app.core.config import settings

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


class InvalidImageTypeError(Exception):
    """Raised when the uploaded file is not a supported image."""


class MediaNotFoundError(Exception):
    """Raised when the stored file is missing."""


class LocalPhotoStorage:
    """File-system backed photo storage."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = Path(root) if root is not None else Path(settings.media_root)

    def save(self, user_id: str, ext: str, content: bytes) -> str:
        if ext not in _IMAGE_EXTENSIONS:
            raise InvalidImageTypeError(ext)
        storage_key = f"{user_id}/{uuid.uuid4().hex}{ext}"
        path = self._root / storage_key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return storage_key

    def open(self, storage_key: str) -> bytes:
        path = (self._root / storage_key).resolve()
        if not path.is_file() or not str(path).startswith(str(self._root.resolve())):
            raise MediaNotFoundError()
        return path.read_bytes()