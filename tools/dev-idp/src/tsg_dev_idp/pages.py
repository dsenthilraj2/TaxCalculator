"""HTML pages for the dev IdP. Every page carries the 'not for production' banner."""

import html

from tsg_dev_idp.config import IdpConfig

BANNER = "DEVELOPMENT IDENTITY PROVIDER — NOT FOR PRODUCTION"

_STYLE = """
  :root { color-scheme: light dark; --accent: #3949ab; }
  body { font-family: system-ui, sans-serif; margin: 0; background: Canvas; color: CanvasText; }
  .banner { background: #b71c1c; color: #fff; text-align: center; padding: 8px;
            font-weight: 700; letter-spacing: .04em; font-size: 13px; }
  main { max-width: 560px; margin: 32px auto; padding: 0 16px; }
  h1 { font-size: 22px; margin-bottom: 4px; }
  p.sub { margin-top: 0; opacity: .75; }
  button.persona { display: block; width: 100%; text-align: left; padding: 12px 14px;
            margin: 8px 0; border-radius: 10px; border: 1px solid #8884; background: transparent;
            color: inherit; font: inherit; cursor: pointer; }
  button.persona:hover { border-color: var(--accent); background: #3949ab14; }
  .name { font-weight: 600; } .meta { font-size: 13px; opacity: .75; }
  .tag { display: inline-block; font-size: 12px; padding: 1px 8px; border-radius: 99px;
         background: #3949ab22; margin-right: 4px; }
  .disabled { background: #b71c1c22; }
"""


def _page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · TSG Dev IdP</title><style>{_STYLE}</style></head>
<body><div class="banner">{BANNER}</div><main><h1>{html.escape(title)}</h1>{body}</main></body>
</html>"""


def picker_page(config: IdpConfig, hidden: dict[str, str]) -> str:
    """The sign-in page: one button per persona."""
    inputs = "".join(
        f"<input type='hidden' name='{html.escape(k)}' value='{html.escape(v)}'>"
        for k, v in hidden.items()
    )
    buttons = []
    for persona in config.personas:
        roles = "".join(f'<span class="tag">{html.escape(r)}</span>' for r in persona.roles)
        client = "all" if persona.tenant_id == "*" else persona.tenant_id
        disabled = '<span class="tag disabled">disabled</span>' if persona.disabled else ""
        buttons.append(
            f"""<button class="persona" type="submit" name="persona"
                value="{html.escape(persona.email)}">
              <div class="name">{html.escape(persona.name)}</div>
              <div class="meta">{html.escape(persona.email)}</div>
              <div class="meta">{roles}<span class="tag">client: {html.escape(client)}</span>
                {disabled} {html.escape(persona.note)}</div>
            </button>"""
        )
    body = (
        "<p class='sub'>Choose a test user to sign in as. No password needed.</p>"
        f"<form method='post' action='/authorize'>{inputs}{''.join(buttons)}</form>"
    )
    return _page("Sign in to TSG Tax Gateway", body)


def home_page(config: IdpConfig) -> str:
    """Overview of the configured personas."""
    rows = "".join(
        f"<li><b>{html.escape(p.name)}</b> &lt;{html.escape(p.email)}&gt; · "
        f"{', '.join(p.roles)} · client {html.escape(p.tenant_id)}"
        f"{' · <i>disabled</i>' if p.disabled else ''}</li>"
        for p in config.personas
    )
    issuer = html.escape(config.issuer)
    body = (
        f"<p>Issuer <code>{issuer}</code> · "
        f"<a href='{issuer}/.well-known/openid-configuration'>discovery</a> · "
        f"<a href='{issuer}/jwks.json'>JWKS</a></p><ul>{rows}</ul>"
    )
    return _page("Test users", body)


def signed_out_page() -> str:
    """Shown when logout has no registered redirect."""
    return _page("Signed out", "<p>You are signed out.</p>")
