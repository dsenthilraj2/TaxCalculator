"""Generic OIDC access-token verification (dev IdP locally, Entra External ID later).

Nothing here is specific to an identity provider: the issuer's discovery document gives
the JWKS URL, and claim names for roles and tenant are configuration.
"""

import asyncio
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

import httpx
import jwt

from tsg_gateway.domain.errors import AuthenticationError, DependencyUnavailableError
from tsg_gateway.domain.identity import Principal, Role
from tsg_gateway.observability.logging import get_logger

logger = get_logger(__name__)

_ALLOWED_ALGORITHMS = ["RS256"]


class JwksSource(Protocol):
    """Provides signing keys by key id."""

    async def keys(self, *, refresh: bool = False) -> Mapping[str, jwt.PyJWK]: ...


class StaticJwksSource:
    """Fixed keys (tests)."""

    def __init__(self, jwks: dict[str, Any]) -> None:
        self._keys = _parse_jwks(jwks)

    async def keys(self, *, refresh: bool = False) -> Mapping[str, jwt.PyJWK]:
        return self._keys


class HttpJwksSource:
    """Keys from the issuer's discovery document, cached and refreshed on unknown key ids."""

    def __init__(
        self,
        issuer: str,
        client: httpx.AsyncClient,
        *,
        ttl_seconds: float = 600,
        min_refresh_seconds: float = 30,
    ) -> None:
        self._discovery_url = issuer.rstrip("/") + "/.well-known/openid-configuration"
        self._client = client
        self._ttl = ttl_seconds
        self._min_refresh = min_refresh_seconds
        self._keys: dict[str, jwt.PyJWK] = {}
        self._fetched_at = 0.0
        self._lock = asyncio.Lock()

    async def keys(self, *, refresh: bool = False) -> Mapping[str, jwt.PyJWK]:
        age = time.monotonic() - self._fetched_at
        stale = not self._keys or age > self._ttl
        # A forced refresh (unknown kid) is rate limited so bad tokens can't hammer the IdP.
        if not stale and not (refresh and age > self._min_refresh):
            return self._keys
        async with self._lock:
            try:
                discovery = await self._client.get(self._discovery_url)
                discovery.raise_for_status()
                jwks = await self._client.get(discovery.json()["jwks_uri"])
                jwks.raise_for_status()
            except (httpx.HTTPError, KeyError, ValueError) as exc:
                logger.warning("oidc.jwks_fetch_failed", error=type(exc).__name__)
                if self._keys:
                    return self._keys
                raise DependencyUnavailableError("Identity provider is unreachable.") from exc
            self._keys = _parse_jwks(jwks.json())
            self._fetched_at = time.monotonic()
            logger.info("oidc.jwks_loaded", keys=len(self._keys))
            return self._keys


def _parse_jwks(jwks: dict[str, Any]) -> dict[str, jwt.PyJWK]:
    return {
        key["kid"]: jwt.PyJWK(key)
        for key in jwks.get("keys", [])
        if key.get("kid") and key.get("alg", "RS256") in _ALLOWED_ALGORITHMS
    }


@dataclass(frozen=True)
class ClaimNames:
    """Which token claims carry roles and the client (they differ between providers)."""

    roles: str = "roles"
    tenant: str = "tenant_id"


class OidcTokenVerifier:
    """Verifies RS256 access tokens: signature, issuer, audience, expiry, required claims."""

    LEEWAY_SECONDS = 30

    def __init__(
        self, *, issuer: str, audience: str, jwks: JwksSource, claims: ClaimNames | None = None
    ) -> None:
        self._issuer = issuer.rstrip("/")
        self._audience = audience
        self._jwks = jwks
        self._claims = claims or ClaimNames()

    async def verify(self, token: str) -> Principal:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as exc:
            raise AuthenticationError("Malformed token.") from exc
        if header.get("alg") not in _ALLOWED_ALGORITHMS:
            raise AuthenticationError("Unsupported token algorithm.")
        kid = header.get("kid", "")
        key = (await self._jwks.keys()).get(kid)
        if key is None:
            key = (await self._jwks.keys(refresh=True)).get(kid)
        if key is None:
            raise AuthenticationError("Token signed with an unknown key.")

        try:
            claims: dict[str, Any] = jwt.decode(
                token,
                key.key,
                algorithms=_ALLOWED_ALGORITHMS,
                audience=self._audience,
                issuer=self._issuer,
                leeway=self.LEEWAY_SECONDS,
                options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationError("Token has expired.") from exc
        except jwt.InvalidAudienceError as exc:
            raise AuthenticationError("Token is not intended for this API.") from exc
        except jwt.InvalidIssuerError as exc:
            raise AuthenticationError("Token issuer is not trusted.") from exc
        except jwt.PyJWTError as exc:
            raise AuthenticationError("Invalid token.") from exc

        raw_roles = claims.get(self._claims.roles) or []
        roles = frozenset(Role(r) for r in raw_roles if r in Role._value2member_map_)
        tenant = claims.get(self._claims.tenant)
        return Principal(
            subject=claims["sub"],
            email=claims.get("email"),
            name=claims.get("name"),
            roles=roles,
            tenant_id=str(tenant) if tenant else None,
        )

    async def is_reachable(self) -> bool:
        try:
            await self._jwks.keys()
        except DependencyUnavailableError:
            return False
        return True
