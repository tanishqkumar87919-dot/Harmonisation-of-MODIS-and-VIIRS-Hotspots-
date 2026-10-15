"""Application configuration and environment settings."""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Core configuration settings loaded from environment variables or defaults.
    Adheres to NFR-05 (Security), NFR-03 (Performance), and docs/06_SYSTEM_ARCHITECTURE.md.
    """

    APP_NAME: str = "Harmonisation of MODIS and VIIRS Hotspots API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    API_V1_PREFIX: str = "/api"
    CORS_ORIGINS: List[str] = ["*"]

    # Upload Security and Storage Constraints (NFR-05)
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = [".csv"]
    STORAGE_DIR: str = "data/storage"

    # Database connection string (optional; defaults to in-memory/sqlite)
    DATABASE_URL: Optional[str] = None

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL or "sqlite:///./modis_viirs.db"

    @database_url.setter
    def database_url(self, value: Optional[str]) -> None:
        self.DATABASE_URL = value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
