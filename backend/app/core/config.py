"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="BACKEND_")

    app_name: str = "fluffy-parakeet"
    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///./app.db"
    presence_ttl_hours: int = 4
    log_level: str = "INFO"
    media_root: str = "./media"
    media_base_url: str = "http://localhost:8000"
    max_photo_upload_bytes: int = 10 * 1024 * 1024
    photo_storage_backend: str = "local"
    minio_endpoint: str = "minio:9000"
    minio_secure: bool = False
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "fluffy-parakeet"
    minio_region: str = "us-east-1"
    minio_public_endpoint: str = "http://localhost:9000"
    minio_url_expiry_seconds: int = 3600


settings = Settings()
