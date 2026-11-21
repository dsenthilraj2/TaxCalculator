import base64
import hashlib
import secrets
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx
import jwt
import pytest

from tsg_dev_idp.app import create_app
from tsg_dev_idp.config import IdpConfig, SigningKey, load_config, load_or_create_key

REDIRECT = "http://127.0.0.1:5173/"


@pytest.fixture
def config() -> IdpConfig:
    return load_config()


@pytest.fixture
def key(tmp_path: Path) -> SigningKey:
    return load_or_create_key(tmp_path)


@pytest.fixture
async def client(config: IdpConfig, key: SigningKey) -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=create_app(config, key))
    return httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8081")


def _pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    digest = hashlib.sha256(verifier.encode()).digest()
    return verifier, base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


async def _sign_in(client: httpx.AsyncClient, persona: str, challenge: str) -> httpx.Response:
    return await client.post(
        "/authorize",
        data={
            "persona": persona,
            "client_id": "tsg-portal",
            "redirect_uri": REDIRECT,
            "code_challenge": challenge,
            "state": "s1",
            "nonce": "n1",
        },
    )


async def test_discovery_and_jwks(client: httpx.AsyncClient, key: SigningKey) -> None:
    discovery = (await client.get("/.well-known/openid-configuration")).json()
    assert discovery["issuer"] == "http://127.0.0.1:8081"
    assert discovery["code_challenge_methods_supported"] == ["S256"]

    jwks = (await client.get("/jwks.json")).json()
    assert jwks["keys"][0]["kid"] == key.kid


async def test_picker_lists_personas_and_banner(client: httpx.AsyncClient) -> None:
    _, challenge = _pkce()
    page = await client.get(
        "/authorize",
        params={"client_id": "tsg-portal", "redirect_uri": REDIRECT, "code_challenge": challenge},
    )
    assert page.status_code == 200
    assert "NOT FOR PRODUCTION" in page.text
    assert "admin@acme.dev.local" in page.text


async def test_rejects_unregistered_redirect_uri(client: httpx.AsyncClient) -> None:
    _, challenge = _pkce()
    page = await client.get(
        "/authorize",
        params={
            "client_id": "tsg-portal",
            "redirect_uri": "https://evil.example/",
            "code_challenge": challenge,
        },
    )
    assert page.status_code == 400


async def test_full_code_flow_issues_valid_tokens(
    client: httpx.AsyncClient, key: SigningKey
) -> None:
    verifier, challenge = _pkce()
    redirect = await _sign_in(client, "admin@acme.dev.local", challenge)
    assert redirect.status_code == 303
    query = parse_qs(urlparse(redirect.headers["location"]).query)
    assert query["state"] == ["s1"]

    response = await client.post(
        "/token",
        data={
            "grant_type": "authorization_code",
            "client_id": "tsg-portal",
            "code": query["code"][0],
            "redirect_uri": REDIRECT,
            "code_verifier": verifier,
        },
    )
    assert response.status_code == 200
    tokens = response.json()
    public_key = jwt.PyJWK(key.public_jwk).key
    access = jwt.decode(
        tokens["access_token"],
        public_key,
        algorithms=["RS256"],
        audience="tsg-gateway",
        issuer="http://127.0.0.1:8081",
    )
    assert access["roles"] == ["ClientAdmin"]
    assert access["tenant_id"] == "acme"
    identity = jwt.decode(
        tokens["id_token"], public_key, algorithms=["RS256"], audience="tsg-portal"
    )
    assert identity["nonce"] == "n1"

    reused = await client.post(
        "/token",
        data={
            "grant_type": "authorization_code",
            "client_id": "tsg-portal",
            "code": query["code"][0],
            "redirect_uri": REDIRECT,
            "code_verifier": verifier,
        },
    )
    assert reused.json()["error"] == "invalid_grant"


async def test_wrong_pkce_verifier_is_rejected(client: httpx.AsyncClient) -> None:
    _, challenge = _pkce()
    redirect = await _sign_in(client, "user@acme.dev.local", challenge)
    code = parse_qs(urlparse(redirect.headers["location"]).query)["code"][0]

    response = await client.post(
        "/token",
        data={
            "grant_type": "authorization_code",
            "client_id": "tsg-portal",
            "code": code,
            "redirect_uri": REDIRECT,
            "code_verifier": "wrong",
        },
    )
    assert response.status_code == 400


async def test_disabled_user_is_refused(client: httpx.AsyncClient) -> None:
    _, challenge = _pkce()
    redirect = await _sign_in(client, "locked@acme.dev.local", challenge)

    query = parse_qs(urlparse(redirect.headers["location"]).query)
    assert query["error"] == ["access_denied"]
    assert "code" not in query


async def test_client_credentials(client: httpx.AsyncClient, key: SigningKey) -> None:
    ok = await client.post(
        "/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "acme-erp",
            "client_secret": "dev-only-acme-erp-secret",
        },
    )
    claims = jwt.decode(
        ok.json()["access_token"],
        jwt.PyJWK(key.public_jwk).key,
        algorithms=["RS256"],
        audience="tsg-gateway",
    )
    assert claims["tenant_id"] == "acme"
    assert claims["roles"] == ["Integration"]

    bad = await client.post(
        "/token",
        data={"grant_type": "client_credentials", "client_id": "acme-erp", "client_secret": "x"},
    )
    assert bad.status_code == 401
