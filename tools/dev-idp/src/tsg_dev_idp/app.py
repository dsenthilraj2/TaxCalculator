"""Minimal OIDC provider: discovery, JWKS, authorize (persona picker), token, userinfo, logout.

Implements only what local development needs: Authorization Code + PKCE (S256) for the
portal and client credentials for machine clients. Sessions are not kept: every sign-in
shows the persona picker, which makes switching users easy.
"""

import base64
import hashlib
import secrets
import time
from dataclasses import dataclass
from typing import Annotated, Any
from urllib.parse import urlencode

import jwt
from fastapi import FastAPI, Form, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from pydantic import BaseModel

from tsg_dev_idp.config import Client, IdpConfig, Persona, SigningKey
from tsg_dev_idp.pages import home_page, picker_page, signed_out_page
from tsg_dev_idp.tokens import Subject, access_token, id_token

CODE_TTL_SECONDS = 120
_NO_STORE = {"Cache-Control": "no-store"}


class AuthorizeQuery(BaseModel):
    """``GET /authorize`` parameters (Authorization Code + PKCE)."""

    client_id: str
    redirect_uri: str
    code_challenge: str
    response_type: str = "code"
    code_challenge_method: str = "S256"
    state: str = ""
    nonce: str = ""
    scope: str = "openid"


class PersonaChoice(BaseModel):
    """``POST /authorize`` form: the persona picked, plus the original request."""

    persona: str
    client_id: str
    redirect_uri: str
    code_challenge: str
    state: str = ""
    nonce: str = ""


class TokenForm(BaseModel):
    """``POST /token`` form."""

    grant_type: str
    client_id: str
    code: str | None = None
    redirect_uri: str | None = None
    code_verifier: str | None = None
    client_secret: str | None = None


@dataclass
class _PendingCode:
    persona: Persona
    client_id: str
    redirect_uri: str
    code_challenge: str
    nonce: str | None
    expires_at: float


def _token_error(error: str, description: str, status: int = 400) -> JSONResponse:
    return JSONResponse({"error": error, "error_description": description}, status_code=status)


def _pkce_matches(verifier: str, challenge: str) -> bool:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    expected = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return secrets.compare_digest(expected, challenge)


class _Provider:
    """Grant logic, kept out of the route functions."""

    def __init__(self, config: IdpConfig, key: SigningKey) -> None:
        self.config = config
        self.key = key
        self._codes: dict[str, _PendingCode] = {}

    def public_client(self, client_id: str, redirect_uri: str) -> Client:
        client = self.config.client(client_id)
        if client is None or client.type != "public":
            raise HTTPException(400, f"Unknown client '{client_id}'.")
        if redirect_uri not in client.redirect_uris:
            raise HTTPException(400, f"redirect_uri '{redirect_uri}' is not registered.")
        return client

    def discovery(self) -> dict[str, Any]:
        base = self.config.issuer
        return {
            "issuer": base,
            "authorization_endpoint": f"{base}/authorize",
            "token_endpoint": f"{base}/token",
            "userinfo_endpoint": f"{base}/userinfo",
            "end_session_endpoint": f"{base}/logout",
            "jwks_uri": f"{base}/jwks.json",
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "client_credentials"],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["RS256"],
            "code_challenge_methods_supported": ["S256"],
            "scopes_supported": ["openid", "profile", "email"],
            "token_endpoint_auth_methods_supported": ["none", "client_secret_post"],
            "claims_supported": ["sub", "email", "name", "roles", "tenant_id"],
        }

    def choose(self, choice: PersonaChoice) -> str:
        """Redirect target after a persona is picked: a code, or ``access_denied``."""
        self.public_client(choice.client_id, choice.redirect_uri)
        user = self.config.persona(choice.persona)
        if user is None:
            raise HTTPException(400, f"Unknown persona '{choice.persona}'.")
        if user.disabled:
            params = {
                "error": "access_denied",
                "error_description": f"User {user.email} is disabled.",
                "state": choice.state,
            }
        else:
            code = secrets.token_urlsafe(24)
            self._codes[code] = _PendingCode(
                persona=user,
                client_id=choice.client_id,
                redirect_uri=choice.redirect_uri,
                code_challenge=choice.code_challenge,
                nonce=choice.nonce or None,
                expires_at=time.time() + CODE_TTL_SECONDS,
            )
            params = {"code": code, "state": choice.state}
        return f"{choice.redirect_uri}?{urlencode(params)}"

    def exchange_code(self, form: TokenForm) -> JSONResponse:
        pending = self._codes.pop(form.code or "", None)
        if pending is None or pending.expires_at < time.time():
            return _token_error("invalid_grant", "Unknown or expired authorization code.")
        if pending.client_id != form.client_id or pending.redirect_uri != form.redirect_uri:
            return _token_error("invalid_grant", "client_id or redirect_uri mismatch.")
        if not form.code_verifier or not _pkce_matches(form.code_verifier, pending.code_challenge):
            return _token_error("invalid_grant", "PKCE verification failed.")
        who = Subject.for_persona(pending.persona, form.client_id)
        body = {
            "access_token": access_token(self.config, self.key, who),
            "id_token": id_token(self.config, self.key, who, pending.nonce),
            "token_type": "Bearer",
            "expires_in": self.config.token_minutes * 60,
            "scope": "openid profile email",
        }
        return JSONResponse(body, headers=_NO_STORE)

    def client_credentials(self, form: TokenForm) -> JSONResponse:
        client = self.config.client(form.client_id)
        authenticated = (
            client is not None
            and client.type == "confidential"
            and client.client_secret is not None
            and secrets.compare_digest(client.client_secret, form.client_secret or "")
        )
        if client is None or not authenticated:
            return _token_error("invalid_client", "Client authentication failed.", 401)
        body = {
            "access_token": access_token(self.config, self.key, Subject.for_client(client)),
            "token_type": "Bearer",
            "expires_in": self.config.token_minutes * 60,
        }
        return JSONResponse(body, headers=_NO_STORE)

    def userinfo(self, authorization: str) -> dict[str, Any]:
        try:
            claims: dict[str, Any] = jwt.decode(
                authorization.removeprefix("Bearer ").strip(),
                jwt.PyJWK(self.key.public_jwk).key,
                algorithms=["RS256"],
                audience=self.config.audience,
                issuer=self.config.issuer,
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(401, "Invalid token.") from exc
        return {k: claims[k] for k in ("sub", "email", "name", "roles", "tenant_id") if k in claims}

    def logout_target(self, post_logout_redirect_uri: str | None, state: str | None) -> str | None:
        allowed = {uri for c in self.config.clients for uri in c.post_logout_redirect_uris}
        if not post_logout_redirect_uri or post_logout_redirect_uri not in allowed:
            return None
        suffix = f"?{urlencode({'state': state})}" if state else ""
        return post_logout_redirect_uri + suffix


def create_app(config: IdpConfig, key: SigningKey) -> FastAPI:
    """Build the provider for ``config``."""
    provider = _Provider(config, key)
    app = FastAPI(title="TSG Dev IdP", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(config.allowed_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.get("/.well-known/openid-configuration")
    async def discovery() -> dict[str, Any]:
        return provider.discovery()

    @app.get("/jwks.json")
    async def jwks() -> dict[str, Any]:
        return {"keys": [key.public_jwk]}

    @app.get("/authorize", response_class=HTMLResponse)
    async def authorize(query: Annotated[AuthorizeQuery, Query()]) -> HTMLResponse:
        provider.public_client(query.client_id, query.redirect_uri)
        if query.response_type != "code" or query.code_challenge_method != "S256":
            raise HTTPException(400, "Only response_type=code with PKCE S256 is supported.")
        hidden = query.model_dump(include={"client_id", "redirect_uri", "code_challenge"})
        hidden |= {"state": query.state, "nonce": query.nonce}
        return HTMLResponse(picker_page(config, hidden))

    @app.post("/authorize")
    async def choose_persona(choice: Annotated[PersonaChoice, Form()]) -> RedirectResponse:
        return RedirectResponse(provider.choose(choice), status_code=303)

    @app.post("/token")
    async def token(form: Annotated[TokenForm, Form()]) -> JSONResponse:
        if form.grant_type == "authorization_code":
            return provider.exchange_code(form)
        if form.grant_type == "client_credentials":
            return provider.client_credentials(form)
        return _token_error("unsupported_grant_type", f"grant_type '{form.grant_type}'.")

    @app.get("/userinfo")
    async def userinfo(authorization: Annotated[str, Header()] = "") -> dict[str, Any]:
        return provider.userinfo(authorization)

    @app.get("/logout")
    async def logout(
        post_logout_redirect_uri: str | None = None, state: str | None = None
    ) -> Response:
        target = provider.logout_target(post_logout_redirect_uri, state)
        if target:
            return RedirectResponse(target, status_code=303)
        return HTMLResponse(signed_out_page())

    @app.get("/", response_class=HTMLResponse)
    async def home() -> HTMLResponse:
        return HTMLResponse(home_page(config))

    return app
