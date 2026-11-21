"""``dev-idp serve`` runs the provider; ``dev-idp token`` prints a bearer token for testing.

Examples:
    dev-idp serve
    dev-idp token --persona admin@acme.dev.local
    dev-idp token --persona user@acme.dev.local --expired
"""

import argparse
import base64
import sys
import time
from urllib.parse import urlparse

import uvicorn

from tsg_dev_idp.app import create_app
from tsg_dev_idp.config import load_config, load_or_create_key
from tsg_dev_idp.pages import BANNER
from tsg_dev_idp.tokens import Subject, TokenOptions, access_token


def _tamper(token: str) -> str:
    """Change one claim without re-signing, so the signature no longer matches."""
    header, payload, signature = token.split(".")
    padded = payload + "=" * (-len(payload) % 4)
    decoded = base64.urlsafe_b64decode(padded).replace(b'"ClientUser"', b'"TsgAdmin"')
    decoded = decoded.replace(b'"ClientAdmin"', b'"TsgAdmin"')
    tampered = base64.urlsafe_b64encode(decoded).rstrip(b"=").decode()
    return f"{header}.{tampered}.{signature}"


def main(argv: list[str] | None = None) -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(prog="dev-idp", description=BANNER)
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("serve", help="Run the provider on 127.0.0.1 (port from the issuer URL)")

    token = commands.add_parser("token", help="Print an access token for a persona")
    token.add_argument("--persona", required=True, help="Persona email from personas.yaml")
    token.add_argument("--client", default="tsg-portal", help="Client id (azp claim)")
    token.add_argument("--minutes", type=int, default=None)
    token.add_argument("--expired", action="store_true", help="Already expired")
    token.add_argument("--wrong-audience", action="store_true", help="aud is not the API")
    token.add_argument("--tampered", action="store_true", help="Signature does not match")

    args = parser.parse_args(argv)
    config = load_config()
    key = load_or_create_key()

    if args.command == "serve":
        port = urlparse(config.issuer).port or 8081
        print(f"\n  {BANNER}\n  Issuer {config.issuer}\n", file=sys.stderr)  # noqa: T201
        uvicorn.run(create_app(config, key), host="127.0.0.1", port=port, log_level="info")
        return

    persona = config.persona(args.persona)
    if persona is None:
        parser.error(f"unknown persona {args.persona!r}")
    options = TokenOptions(
        minutes=60 if args.expired else args.minutes,
        audience="not-the-gateway" if args.wrong_audience else None,
        issued_at=int(time.time()) - 7200 if args.expired else None,
    )
    value = access_token(config, key, Subject.for_persona(persona, args.client), options)
    print(_tamper(value) if args.tampered else value)  # noqa: T201


if __name__ == "__main__":
    main()
