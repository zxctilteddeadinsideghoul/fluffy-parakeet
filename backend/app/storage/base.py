"""Photo storage abstraction: local disk or S3-compatible object store."""

from __future__ import annotations

from typing import Protocol


class PhotoStorage(Protocol):
    """Persists uploaded photos and exposes them via public URLs."""

    def save(self, user_id: str, ext: str, content: bytes) -> str:
        """Store the file and return its storage key."""
        ...

    def open(self, storage_key: str) -> bytes:
        """Read the stored file back by its key."""
        ...

    def public_url(self, storage_key: str, photo_id: str) -> str:
        """Build a URL the browser can fetch the photo from."""
        ...

    def ensure_bucket(self) -> None:
        """Prepare the underlying store; a no-op where not applicable."""
        ...