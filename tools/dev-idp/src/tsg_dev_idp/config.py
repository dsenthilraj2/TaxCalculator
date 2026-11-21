"""Load personas.yaml and the signing key."""

import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

_TOOL_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _TOOL_ROOT.parents[1]

DEFAULT_CONFIG = Path(os.environ.get("DEV_IDP_CONFIG", _TOOL_ROOT / "personas.yaml"))
DEFAULT_KEY_DIR = Path(os.environ.get("DEV_IDP_KEY_DIR", _REPO_ROOT / ".localdata" / "idp"))


@dataclass(frozen=True)
class Persona:
    """A test user."""

    email: str
    name: str
    roles: tuple[str, ...]
    tenant_id: str
    disabled: bool = False
    note: str = ""

    @property
    def subject(self) -> str:
        return f"dev|{self.email}"


@dataclass(frozen=True)
class Client:
    """An OAuth client: the portal (public, PKCE) or a machine client (secret)."""

    client_id: str
    type: str
    redirect_uris: tuple[str, ...] = ()
    post_logout_redirect_uris: tuple[str, ...] = ()
    client_secret: str | None = None
    tenant_id: str | None = None
    roles: tuple[str, ...] = ()


@dataclass(frozen=True)
class IdpConfig:
    """Everything the provider needs."""

    issuer: str
    audience: str
    token_minutes: int
    personas: tuple[Persona, ...]
    clients: tuple[Client, ...]
    allowed_origins: tuple[str, ...] = field(default=())

    def persona(self, email: str) -> Persona | None:
        return next((p for p in self.personas if p.email == email), None)

    def client(self, client_id: str) -> Client | None:
        return next((c for c in self.clients if c.client_id == client_id), None)


def load_config(path: Path = DEFAULT_CONFIG) -> IdpConfig:
    """Read personas.yaml."""
    raw: dict[str, Any] = yaml.safe_load(path.read_text("utf-8"))
    personas = tuple(
        Persona(
            email=p["email"],
            name=p["name"],
            roles=tuple(p["roles"]),
            tenant_id=str(p["tenant_id"]),
            disabled=bool(p.get("disabled", False)),
            note=p.get("note", ""),
        )
        for p in raw["personas"]
    )
    clients = tuple(
        Client(
            client_id=c["client_id"],
            type=c["type"],
            redirect_uris=tuple(c.get("redirect_uris", ())),
            post_logout_redirect_uris=tuple(c.get("post_logout_redirect_uris", ())),
            client_secret=c.get("client_secret"),
            tenant_id=c.get("tenant_id"),
            roles=tuple(c.get("roles", ())),
        )
        for c in raw["clients"]
    )
    origins = sorted({_origin(uri) for client in clients for uri in client.redirect_uris})
    return IdpConfig(
        issuer=raw["issuer"].rstrip("/"),
        audience=raw["audience"],
        token_minutes=int(raw.get("token_minutes", 60)),
        personas=personas,
        clients=clients,
        allowed_origins=tuple(origins),
    )


def _origin(uri: str) -> str:
    """``http://127.0.0.1:5173/`` -> ``http://127.0.0.1:5173``."""
    scheme, _, host = uri.split("/", 3)[:3]
    return f"{scheme}//{host}"


@dataclass(frozen=True)
class SigningKey:
    """RSA key used to sign tokens, with its public JWK."""

    private_pem: bytes
    kid: str
    public_jwk: dict[str, Any]


def load_or_create_key(key_dir: Path = DEFAULT_KEY_DIR) -> SigningKey:
    """Load the dev signing key, generating it on first run."""
    key_dir.mkdir(parents=True, exist_ok=True)
    path = key_dir / "signing-key.pem"
    if not path.exists():
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        path.write_bytes(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
        path.chmod(0o600)
    pem = path.read_bytes()
    private_key = serialization.load_pem_private_key(pem, password=None)
    if not isinstance(private_key, rsa.RSAPrivateKey):
        raise TypeError("Dev IdP signing key must be RSA")
    public_der = private_key.public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    kid = hashlib.sha256(public_der).hexdigest()[:16]
    jwk: dict[str, Any] = RSAAlgorithm.to_jwk(private_key.public_key(), as_dict=True)
    jwk.update({"kid": kid, "use": "sig", "alg": "RS256"})
    return SigningKey(private_pem=pem, kid=kid, public_jwk=jwk)
