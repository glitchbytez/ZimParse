"""Application configuration loaded from environment variables / `.env`."""

from enum import Enum
from functools import lru_cache

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class LogFormat(str, Enum):
    JSON = "json"
    TEXT = "text"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "ZimParse"
    app_version: str = "0.1.0"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=list)

    # --- Logging ---
    log_level: str = "INFO"
    log_format: LogFormat = LogFormat.JSON

    # --- Anthropic / Claude ---
    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = "claude-sonnet-5-5"
    anthropic_timeout_seconds: float = 60.0
    anthropic_max_retries: int = 3

    # --- Persistence ---
    database_url: str = "postgresql+psycopg://zimparse:zimparse@localhost:5432/zimparse"
    redis_url: str = "redis://localhost:6379/0"

    # --- Storage ---
    storage_backend: str = "local"  # "local" | "azure"
    local_storage_path: str = "./data/uploads"
    azure_storage_connection_string: SecretStr | None = None
    azure_storage_container: str = "zimparse-uploads"

    # --- Uploads ---
    max_upload_size_mb: int = Field(default=10, gt=0)

    @property
    def is_production(self) -> bool:
        return self.environment is Environment.PRODUCTION

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @model_validator(mode="after")
    def _validate_production(self) -> "Settings":
        if self.is_production:
            if self.anthropic_api_key is None or not self.anthropic_api_key.get_secret_value():
                raise ValueError("ANTHROPIC_API_KEY must be set in production")
            if self.debug:
                raise ValueError("DEBUG must be disabled in production")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (use as a FastAPI dependency)."""
    return Settings()
