# TSG Tax Gateway

Connects ERP and eCommerce systems to tax calculators. The specification is in [spec/](spec/README.md).

## Demo in one command

```bash
scripts/demo.sh start    # MongoDB + dev sign-in + API + UI (installs and seeds demo data on first run)
scripts/demo.sh stop     # stops everything, including MongoDB
```

Then open **http://127.0.0.1:5173**, click **Sign in** and pick a test user. Other commands:
`status`, `restart`, `logs`, `seed`. (`make demo` / `make demo-stop` do the same.)

| What | Where |
|---|---|
| UI (dashboard, products & tax categories, sample calculator, countries & rates) | http://127.0.0.1:5173 |
| API docs (Swagger) | http://127.0.0.1:8000/docs |
| Dev sign-in (test users, not for production) | http://127.0.0.1:8081 |
| Logs | `.localdata/logs/` |
| MongoDB data | `.localdata/mongo/` (MongoDB itself lives in `~/.local/share/tsg-mongodb`) |

No Docker, sudo or cloud account is needed. MongoDB 8 is downloaded from mongodb.org on first run.

### Test users (dev sign-in)

| User | Role | Sees | Can edit setup |
|---|---|---|---|
| TSG Admin | TsgAdmin | Any client (picker in the top bar) | Yes |
| TSG Analyst | TsgAnalyst | Any client | No |
| Alex Acme (admin) | ClientAdmin | Acme | Yes |
| Uma Acme (user) | ClientUser | Acme | No |
| Ben Beta (admin) | ClientAdmin | Beta | Yes |
| Lee Locked | ClientUser (disabled) | Sign-in is refused | — |

Defined in [tools/dev-idp/personas.yaml](tools/dev-idp/personas.yaml). For API calls from the
command line: `make token PERSONA=admin@acme.dev.local` prints a bearer token.

## Prerequisites

[uv](https://docs.astral.sh/uv/) (installs Python 3.13 itself), Node 22, curl, make.

## Development

| Command | Does |
|---|---|
| `make setup` | Python 3.13, backend dependencies, pre-commit hooks |
| `make web-install` | UI dependencies |
| `make db` / `make db-stop` | Start / stop local MongoDB only |
| `make run` | API with auto-reload (port 8000) |
| `make idp` | Dev identity provider (port 8081) |
| `make token PERSONA=…` | Print a test access token |
| `make web` | UI dev server (port 5173, proxies `/v1` to the API) |
| `make seed` | Load demo products, group mappings and sample calculations |
| `make check` | Backend: ruff, mypy (strict), import-linter |
| `make test` / `make test-int` | Backend tests without / with MongoDB |
| `make web-check` | UI: TypeScript, oxlint, vitest |
| `make openapi` | Re-export the OpenAPI spec and regenerate the UI's typed client |

## Layout

```
spec/          specification (start with spec/README.md)
backend/       Python 3.13 · FastAPI · hexagonal layout (see backend/README.md)
web/portal/    React + TypeScript + MUI
scripts/       mongodb.sh (local MongoDB), demo.sh (whole stack)
tools/         local-only tools: dev-idp (sign-in); simulators planned
```
