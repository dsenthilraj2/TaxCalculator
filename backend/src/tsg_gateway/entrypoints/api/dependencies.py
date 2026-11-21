"""Request dependencies: wired services, the verified caller, and the client acted for."""

from typing import Annotated, cast

import structlog
from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from tsg_gateway.bootstrap import Services
from tsg_gateway.domain.errors import AuthenticationError
from tsg_gateway.domain.identity import Principal
from tsg_gateway.settings import Settings

TENANT_HEADER = "X-TSG-Tenant"

_bearer = HTTPBearer(auto_error=False, description="Access token from the identity provider")


def get_services(request: Request) -> Services:
    """The services wired by the composition root."""
    return cast(Services, request.app.state.services)


def get_settings(request: Request) -> Settings:
    """The settings the app was built with."""
    return cast(Settings, request.app.state.settings)


async def get_principal(
    services: Annotated[Services, Depends(get_services)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Principal:
    """The verified caller. Every client endpoint requires a valid bearer token."""
    if credentials is None:
        raise AuthenticationError("Sign in required: missing bearer token.")
    principal = await services.token_verifier.verify(credentials.credentials)
    structlog.contextvars.bind_contextvars(subject=principal.subject)
    return principal


def get_tenant_id(
    principal: Annotated[Principal, Depends(get_principal)],
    settings: Annotated[Settings, Depends(get_settings)],
    tenant: Annotated[str | None, Header(alias=TENANT_HEADER)] = None,
) -> str:
    """The client this request acts for: from the token, or chosen by TSG staff."""
    tenant_id = principal.resolve_tenant(tenant, settings.tenant_ids)
    structlog.contextvars.bind_contextvars(tenant_id=tenant_id)
    return tenant_id


def get_setup_writer_tenant(
    principal: Annotated[Principal, Depends(get_principal)],
    tenant_id: Annotated[str, Depends(get_tenant_id)],
) -> str:
    """The client, for requests that change tax setup (admins only)."""
    principal.require_setup_writer()
    return tenant_id


ServicesDep = Annotated[Services, Depends(get_services)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
PrincipalDep = Annotated[Principal, Depends(get_principal)]
TenantDep = Annotated[str, Depends(get_tenant_id)]
SetupWriterDep = Annotated[str, Depends(get_setup_writer_tenant)]
