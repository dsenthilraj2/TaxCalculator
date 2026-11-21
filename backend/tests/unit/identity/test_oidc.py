import httpx
import pytest
import respx

from tests.support.auth import ISSUER, JWKS, token
from tsg_gateway.adapters.identity.oidc import HttpJwksSource, OidcTokenVerifier
from tsg_gateway.domain.errors import AuthenticationError, DependencyUnavailableError
from tsg_gateway.domain.identity import Role
from tsg_gateway.settings import AppEnv, Settings

DISCOVERY = f"{ISSUER}/.well-known/openid-configuration"
JWKS_URL = f"{ISSUER}/jwks.json"


def _verifier(client: httpx.AsyncClient) -> OidcTokenVerifier:
    return OidcTokenVerifier(
        issuer=ISSUER,
        audience="tsg-gateway",
        jwks=HttpJwksSource(ISSUER, client, min_refresh_seconds=0),
    )


@respx.mock
async def test_fetches_keys_via_discovery_and_caches_them() -> None:
    discovery = respx.get(DISCOVERY).respond(json={"jwks_uri": JWKS_URL})
    jwks = respx.get(JWKS_URL).respond(json=JWKS)
    async with httpx.AsyncClient() as client:
        verifier = _verifier(client)

        first = await verifier.verify(token(["ClientAdmin", "Unknown"], "acme", email="a@x"))
        await verifier.verify(token(["ClientUser"], "beta"))

    assert first.roles == frozenset({Role.CLIENT_ADMIN})
    assert first.tenant_id == "acme"
    assert first.email == "a@x"
    assert discovery.call_count == 1
    assert jwks.call_count == 1


@respx.mock
async def test_unknown_kid_triggers_one_refresh_then_fails() -> None:
    respx.get(DISCOVERY).respond(json={"jwks_uri": JWKS_URL})
    jwks = respx.get(JWKS_URL).respond(json=JWKS)
    async with httpx.AsyncClient() as client:
        verifier = _verifier(client)
        await verifier.verify(token(["ClientUser"], "acme"))

        with pytest.raises(AuthenticationError, match="unknown key"):
            await verifier.verify(token(["ClientUser"], "acme", kid="rotated"))

    assert jwks.call_count == 2


@respx.mock
async def test_unreachable_identity_provider() -> None:
    respx.get(DISCOVERY).mock(side_effect=httpx.ConnectError("refused"))
    async with httpx.AsyncClient() as client:
        verifier = _verifier(client)

        assert await verifier.is_reachable() is False
        with pytest.raises(DependencyUnavailableError):
            await verifier.verify(token(["ClientUser"], "acme"))


def test_refuses_local_identity_provider_outside_local() -> None:
    with pytest.raises(ValueError, match="only allowed when"):
        Settings(_env_file=None, app_env=AppEnv.PROD, oidc_issuer="http://127.0.0.1:8081")

    deployed = Settings(
        _env_file=None, app_env=AppEnv.PROD, oidc_issuer="https://login.example.com"
    )
    assert deployed.oidc_issuer == "https://login.example.com"
