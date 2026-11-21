"""Token minting, shared by the HTTP provider and the CLI."""

import time
from dataclasses import dataclass
from typing import Any

import jwt

from tsg_dev_idp.config import Client, IdpConfig, Persona, SigningKey


@dataclass(frozen=True)
class Subject:
    """Who a token is for: a persona signed in through a client, or a machine client."""

    subject: str
    roles: tuple[str, ...]
    tenant_id: str | None
    client_id: str
    email: str | None = None
    name: str | None = None

    @classmethod
    def for_persona(cls, persona: Persona, client_id: str) -> "Subject":
        return cls(
            subject=persona.subject,
            roles=persona.roles,
            tenant_id=persona.tenant_id,
            client_id=client_id,
            email=persona.email,
            name=persona.name,
        )

    @classmethod
    def for_client(cls, client: Client) -> "Subject":
        return cls(
            subject=f"client|{client.client_id}",
            roles=client.roles,
            tenant_id=client.tenant_id,
            client_id=client.client_id,
        )


@dataclass(frozen=True)
class TokenOptions:
    """Overrides used by the CLI to mint deliberately broken tokens."""

    minutes: int | None = None
    audience: str | None = None
    issued_at: int | None = None


def _sign(claims: dict[str, Any], key: SigningKey) -> str:
    return jwt.encode(claims, key.private_pem, algorithm="RS256", headers={"kid": key.kid})


def _identity_claims(who: Subject) -> dict[str, Any]:
    claims: dict[str, Any] = {"roles": list(who.roles), "tenant_id": who.tenant_id}
    if who.email:
        claims["email"] = who.email
    if who.name:
        claims["name"] = who.name
    return claims


def access_token(
    config: IdpConfig, key: SigningKey, who: Subject, options: TokenOptions | None = None
) -> str:
    """An access token for the gateway API (``aud`` = the API)."""
    options = options or TokenOptions()
    now = options.issued_at if options.issued_at is not None else int(time.time())
    minutes = options.minutes if options.minutes is not None else config.token_minutes
    claims: dict[str, Any] = {
        "iss": config.issuer,
        "sub": who.subject,
        "aud": options.audience or config.audience,
        "iat": now,
        "nbf": now,
        "exp": now + 60 * minutes,
        "azp": who.client_id,
        **_identity_claims(who),
    }
    return _sign(claims, key)


def id_token(config: IdpConfig, key: SigningKey, who: Subject, nonce: str | None) -> str:
    """An OIDC ID token for the portal (``aud`` = the client)."""
    now = int(time.time())
    claims: dict[str, Any] = {
        "iss": config.issuer,
        "sub": who.subject,
        "aud": who.client_id,
        "iat": now,
        "exp": now + 60 * config.token_minutes,
        **_identity_claims(who),
    }
    if nonce:
        claims["nonce"] = nonce
    return _sign(claims, key)
