"""Application configuration — centralized, typed, fail-fast."""

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """All config from environment variables, validated at startup."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "Pet Tracker"
    app_version: str = "0.1.0"
    debug: bool = False
    port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./pet_tracker.db"
    db_pool_size: int = 10
    db_echo: bool = False

    # Auth
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Logging
    log_level: str = "INFO"


settings = Settings()
