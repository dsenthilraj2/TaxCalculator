"""Application settings loaded from the environment (12-factor)."""

from enum import StrEnum
from functools import lru_cache
from urllib.parse import urlparse

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from tsg_gateway.observability.logging import LogFormat

_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


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

    # Known clients. Becomes the tenant catalog once tenant management exists.
    tenants: str = "acme,beta"

    # OIDC: the dev IdP locally (tools/dev-idp), Entra External ID in the cloud.
    oidc_issuer: str = "http://127.0.0.1:8081"
    oidc_audience: str = "tsg-gateway"
    oidc_roles_claim: str = "roles"
    oidc_tenant_claim: str = "tenant_id"

    @model_validator(mode="after")
    def _refuse_local_identity_provider_outside_local(self) -> "Settings":
        """REQ-DEV-2: the dev IdP must never be trusted by a deployed environment."""
        host = urlparse(self.oidc_issuer).hostname or ""
        if self.app_env not in {AppEnv.LOCAL, AppEnv.TEST} and host in _LOCAL_HOSTS:
            raise ValueError(
                f"TSG_OIDC_ISSUER points to {host}, which is only allowed when "
                f"TSG_APP_ENV is local or test (it is {self.app_env.value})."
            )
        return self

    @property
    def is_non_production(self) -> bool:
        """True for environments where dev-only features may be enabled."""
        return self.app_env in {AppEnv.LOCAL, AppEnv.TEST, AppEnv.DEV}

    @property
    def tenant_ids(self) -> list[str]:
        """Parsed ``tenants``."""
        return [tenant.strip() for tenant in self.tenants.split(",") if tenant.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
