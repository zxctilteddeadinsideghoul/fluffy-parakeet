"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="BACKEND_")

    app_name: str = "fluffy-parakeet"
    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///./app.db"
    presence_ttl_hours: int = 4
    log_level: str = "INFO"


settings = Settings()
