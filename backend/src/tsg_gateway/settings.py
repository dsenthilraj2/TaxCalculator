"""Application settings loaded from the environment (12-factor)."""

from enum import StrEnum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(StrEnum):
    """Deployment environment."""

    LOCAL = "local"
    TEST = "test"
    DEV = "dev"
    PROD = "prod"


class Cloud(StrEnum):
    """Adapter profile selected by the composition root."""

    LOCAL = "local"
    AZURE = "azure"
    AWS = "aws"


class Settings(BaseSettings):
    """Settings shared by every entry point."""

    model_config = SettingsConfigDict(
        env_prefix="TSG_",
        env_file=".env.local",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: AppEnv = AppEnv.LOCAL
    cloud: Cloud = Cloud.LOCAL
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
