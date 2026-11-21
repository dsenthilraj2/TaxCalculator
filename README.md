# TSG Tax Gateway

Connects ERP and eCommerce systems to tax calculators. The specification is in [spec/](spec/README.md).

## Demo in one command

```bash
scripts/demo.sh start    # MongoDB + API + UI (installs and seeds demo data on first run)
scripts/demo.sh stop     # stops everything, including MongoDB
```

Then open **http://127.0.0.1:5173**. Other commands: `status`, `restart`, `logs`, `seed`.
(`make demo` / `make demo-stop` do the same.)

| What | Where |
|---|---|
| UI (dashboard, products & tax categories, sample calculator, countries & rates) | http://127.0.0.1:5173 |
| API docs (Swagger) | http://127.0.0.1:8000/docs |
| Logs | `.localdata/logs/` |
| MongoDB data | `.localdata/mongo/` (MongoDB itself lives in `~/.local/share/tsg-mongodb`) |

No Docker, sudo or cloud account is needed. MongoDB 8 is downloaded from mongodb.org on first run.
Use the **Client (dev only)** picker in the top bar to switch between the demo clients (Acme, Beta).

## Prerequisites

[uv](https://docs.astral.sh/uv/) (installs Python 3.13 itself), Node 22, curl, make.

## Development

| Command | Does |
|---|---|
| `make setup` | Python 3.13, backend dependencies, pre-commit hooks |
| `make web-install` | UI dependencies |
| `make db` / `make db-stop` | Start / stop local MongoDB only |
| `make run` | API with auto-reload (port 8000) |
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
tools/         local-only tools (dev IdP, simulators) — planned
```
