"""Identity port: turn a bearer token into a verified principal."""

from typing import Protocol

from tsg_gateway.domain.identity import Principal


class TokenVerifier(Protocol):
    """Verifies access tokens. Raises ``AuthenticationError`` for any invalid token."""

    async def verify(self, token: str) -> Principal: ...

    async def is_reachable(self) -> bool:
        """Whether the identity provider's keys can be fetched (readiness)."""
        ...
