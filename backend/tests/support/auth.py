"""Test tokens signed with a throwaway RSA key, and a verifier that trusts only that key.

Mirrors spec/10-local-development.md §4.3: API tests never call the identity provider.
"""

import time
from typing import Any

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from tsg_gateway.adapters.identity.oidc import OidcTokenVerifier, StaticJwksSource

ISSUER = "http://127.0.0.1:8081"
AUDIENCE = "tsg-gateway"
KID = "test-key"

_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_PRIVATE_PEM = _private_key.private_bytes(
    serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
)
_jwk: dict[str, Any] = RSAAlgorithm.to_jwk(_private_key.public_key(), as_dict=True)
_jwk.update({"kid": KID, "alg": "RS256", "use": "sig"})
JWKS: dict[str, Any] = {"keys": [_jwk]}

_other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_OTHER_PEM = _other_key.private_bytes(
    serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
)


def test_verifier() -> OidcTokenVerifier:
    """A verifier that trusts only the test key."""
    return OidcTokenVerifier(issuer=ISSUER, audience=AUDIENCE, jwks=StaticJwksSource(JWKS))


def token(
    roles: list[str],
    tenant_id: str | None,
    *,
    subject: str = "user-1",
    issuer: str = ISSUER,
    audience: str = AUDIENCE,
    expires_in: int = 3600,
    kid: str = KID,
    signed_by_other_key: bool = False,
    **extra: Any,
) -> str:
    """Mint an access token. Defaults produce a valid token."""
    now = int(time.time())
    claims: dict[str, Any] = {
        "iss": issuer,
        "aud": audience,
        "sub": subject,
        "iat": now - 60,
        "exp": now + expires_in,
        "roles": roles,
        "tenant_id": tenant_id,
        **extra,
    }
    key = _OTHER_PEM if signed_by_other_key else _PRIVATE_PEM
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": kid})


def bearer(value: str, tenant: str | None = None) -> dict[str, str]:
    """Request headers with a bearer token (and an optional X-TSG-Tenant)."""
    headers = {"Authorization": f"Bearer {value}"}
    if tenant:
        headers["X-TSG-Tenant"] = tenant
    return headers


ACME_ADMIN = bearer(token(["ClientAdmin"], "acme", subject="admin@acme"))
ACME_USER = bearer(token(["ClientUser"], "acme", subject="user@acme"))
BETA_ADMIN = bearer(token(["ClientAdmin"], "beta", subject="admin@beta"))
TSG_ADMIN_TOKEN = token(["TsgAdmin"], "*", subject="tsg.admin")
TSG_ANALYST_TOKEN = token(["TsgAnalyst"], "*", subject="tsg.analyst")
