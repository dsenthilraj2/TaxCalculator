"""Application settings loaded from the environment (12-factor)."""

from enum import StrEnum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from tsg_gateway.observability.logging import LogFormat


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


class Store(StrEnum):
    """Where data is kept."""

    MEMORY = "memory"
    MONGO = "mongo"


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
    service_name: str = "tsg-gateway"
    log_level: str = "INFO"
    log_format: LogFormat = LogFormat.CONSOLE
    host: str = "127.0.0.1"
    port: int = 8000

    store: Store = Store.MONGO
    mongo_uri: str = "mongodb://127.0.0.1:27017/?replicaSet=rs0&directConnection=true"
    mongo_database: str = "tsg_local"

    # Clients selectable with the X-TSG-Tenant header (local/test/dev only, until OIDC login).
    dev_tenants: str = "acme,beta"

    @property
    def is_non_production(self) -> bool:
        """True for environments where dev-only features may be enabled."""
        return self.app_env in {AppEnv.LOCAL, AppEnv.TEST, AppEnv.DEV}

    @property
    def dev_tenant_ids(self) -> list[str]:
        """Parsed ``dev_tenants``."""
        return [tenant.strip() for tenant in self.dev_tenants.split(",") if tenant.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
