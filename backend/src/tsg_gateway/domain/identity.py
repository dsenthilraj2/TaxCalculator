"""Who is calling: the principal derived from a verified token, and what it may do."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from tsg_gateway.domain.errors import PermissionDeniedError

ALL_TENANTS = "*"


class Role(StrEnum):
    """Roles carried in the token (spec/10-local-development.md §4.2)."""

    TSG_ADMIN = "TsgAdmin"
    TSG_ANALYST = "TsgAnalyst"
    CLIENT_ADMIN = "ClientAdmin"
    CLIENT_USER = "ClientUser"
    INTEGRATION = "Integration"


_STAFF_ROLES = frozenset({Role.TSG_ADMIN, Role.TSG_ANALYST})
_SETUP_WRITERS = frozenset({Role.TSG_ADMIN, Role.CLIENT_ADMIN})


class Principal(BaseModel):
    """A verified caller: a person (portal) or a machine client (ERP integration)."""

    model_config = ConfigDict(frozen=True)

    subject: str
    email: str | None = None
    name: str | None = None
    roles: frozenset[Role]
    tenant_id: str | None = None

    @property
    def is_tsg_staff(self) -> bool:
        """TSG staff can act for any client they choose."""
        return bool(self.roles & _STAFF_ROLES)

    @property
    def can_edit_setup(self) -> bool:
        """May change products, groups and tax settings."""
        return bool(self.roles & _SETUP_WRITERS)

    def accessible_tenants(self, known_tenants: list[str]) -> list[str]:
        """Clients this principal may act for."""
        if self.is_tsg_staff:
            return list(known_tenants)
        return [self.tenant_id] if self.tenant_id in known_tenants else []

    def resolve_tenant(self, requested: str | None, known_tenants: list[str]) -> str:
        """The client a request acts for.

        Staff must name a client; everyone else acts for the client in their token and
        may not name a different one.
        """
        if self.is_tsg_staff:
            if not requested:
                raise PermissionDeniedError("Choose a client (X-TSG-Tenant header).")
            if requested not in known_tenants:
                raise PermissionDeniedError(f"Unknown client '{requested}'.")
            return requested
        tenant = self.tenant_id
        if not tenant or tenant == ALL_TENANTS or tenant not in known_tenants:
            raise PermissionDeniedError("Your account is not linked to a client.")
        if requested and requested != tenant:
            raise PermissionDeniedError("You can only access your own client.")
        return tenant

    def require_setup_writer(self) -> None:
        """Raise unless this principal may change tax setup."""
        if not self.can_edit_setup:
            raise PermissionDeniedError("Your role can view tax setup but not change it.")
