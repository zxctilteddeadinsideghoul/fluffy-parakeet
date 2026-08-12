"""Service tests for the MinIO photo storage backend."""

from io import BytesIO

from app.storage.minio_storage import MinioPhotoStorage


class FakeResponse:
    def __init__(self, data: bytes) -> None:
        self._data = data
        self.released = False
        self.closed = False

    def read(self) -> bytes:
        return self._data

    def close(self) -> None:
        self.closed = True

    def release_conn(self) -> None:
        self.released = True


class FakeMinioClient:
    def __init__(self, presigned: str = "") -> None:
        self.buckets = set()
        self.objects: dict[str, bytes] = {}
        self.presigned = presigned

    def bucket_exists(self, bucket: str) -> bool:
        return bucket in self.buckets

    def make_bucket(self, bucket: str) -> None:
        self.buckets.add(bucket)

    def put_object(self, bucket, key, data: BytesIO, length, content_type) -> None:
        self.objects[key] = data.read()

    def get_object(self, bucket, key):
        return FakeResponse(self.objects[key])

    def presigned_get_object(self, bucket, key, expires) -> str:
        return self.presigned


def make_storage(
    client: FakeMinioClient | None = None, presign_client: FakeMinioClient | None = None
) -> MinioPhotoStorage:
    return MinioPhotoStorage(
        client or FakeMinioClient(),
        endpoint="minio:9000",
        bucket="fluffy-parakeet",
        public_endpoint="http://localhost:9000",
        url_expiry_seconds=3600,
        presign_client=presign_client or FakeMinioClient(),
    )


def test_ensure_bucket_creates_missing_bucket():
    client = FakeMinioClient()
    storage = make_storage(client)

    storage.ensure_bucket()

    assert "fluffy-parakeet" in client.buckets


def test_save_puts_object_into_bucket():
    client = FakeMinioClient()
    storage = make_storage(client)

    key = storage.save("user-1", ".png", b"png-data")

    assert key == "user-1/" + key.split("/", 1)[1]
    assert client.objects[key] == b"png-data"
    assert len(client.objects) == 1


def test_open_reads_object_back():
    client = FakeMinioClient()
    storage = make_storage(client)
    key = storage.save("user-1", ".png", b"payload")

    data = storage.open(key)

    assert data == b"payload"


def test_public_url_comes_from_presigning_client():
    presign = FakeMinioClient(
        presigned="http://localhost:9000/bucket/key?X-Amz-Signature=abc"
    )
    storage = make_storage(presign_client=presign)

    url = storage.public_url("user-1/key.png", "photo-id")

    assert url == "http://localhost:9000/bucket/key?X-Amz-Signature=abc"