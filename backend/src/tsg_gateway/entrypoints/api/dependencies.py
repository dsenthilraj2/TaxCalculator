"""Request dependencies: the wired services and the calling client (tenant)."""

from typing import Annotated, cast

import structlog
from fastapi import Depends, Header, HTTPException, Request
from starlette import status

from tsg_gateway.bootstrap import Services
from tsg_gateway.settings import Settings

TENANT_HEADER = "X-TSG-Tenant"


def get_services(request: Request) -> Services:
    """The services wired by the composition root."""
    return cast(Services, request.app.state.services)


def get_settings(request: Request) -> Settings:
    """The settings the app was built with."""
    return cast(Settings, request.app.state.settings)


def get_tenant_id(
    settings: Annotated[Settings, Depends(get_settings)],
    tenant: Annotated[str | None, Header(alias=TENANT_HEADER)] = None,
) -> str:
    """Resolve the calling client.

    Until OIDC login exists, local/test/dev accept a known client in the ``X-TSG-Tenant``
    header. Production rejects every request here, so this can never ship by accident.
    """
    if not settings.is_non_production:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication is not configured.")
    if not tenant:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Missing {TENANT_HEADER} header.")
    if tenant not in settings.dev_tenant_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Unknown client '{tenant}'.")
    structlog.contextvars.bind_contextvars(tenant_id=tenant)
    return tenant


ServicesDep = Annotated[Services, Depends(get_services)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
TenantDep = Annotated[str, Depends(get_tenant_id)]
