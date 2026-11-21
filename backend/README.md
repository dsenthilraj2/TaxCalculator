# TSG Tax Gateway — Backend

Python 3.13 · FastAPI · Pydantic v2 · hexagonal (ports and adapters) layout.
The design is in [../spec/08-architecture.md](../spec/08-architecture.md) and [../spec/10-local-development.md](../spec/10-local-development.md).

## Quick start

```bash
make setup    # from the repo root: installs Python 3.13 via uv, dependencies, pre-commit hooks
make check    # ruff, mypy, import-linter
make test     # unit + contract tests (no Docker needed)
make run      # API on http://127.0.0.1:8000 (docs at /docs)
```

## Endpoints

| Path | Purpose |
|---|---|
| `GET /health`, `GET /health/ready` | Liveness; readiness (includes MongoDB ping) |
| `GET /v1/tax-categories` | TSG tax categories |
| `GET/PUT/DELETE /v1/products[/{sku}]`, `POST /v1/products/import` | Client products |
| `GET/PUT/DELETE /v1/product-groups[/{group}]` | Product group → category mappings |
| `GET/PUT /v1/tax-settings` | Client default category |
| `POST /v1/tax-categories/resolve`, `GET /v1/tax-setup/summary` | Category lookup; setup counts |
| `POST /v1/tax/calculate`, `GET /v1/tax/jurisdictions` | Sample calculator (TSG rules engine) |
| `GET /v1/calculations/recent`, `GET /v1/usage/summary` | Recent activity; monthly usage |
| `GET /v1/dev/tenants`, `GET /v1/dev/scenarios` | Dev only: demo clients; documented test scenarios |
| `GET /docs` | Swagger UI (local/test/dev only) |

Client endpoints need the `X-TSG-Tenant` header (local/test/dev only, until OIDC login).

Every response carries `X-Correlation-Id` (the caller's value if it's safe, otherwise a new one). Errors are RFC 9457 `application/problem+json` and include `correlationId`.

## Logging

- `TSG_LOG_FORMAT=console` (readable, local) or `json` (cloud). `TSG_LOG_LEVEL` sets the level.
- One `request.completed` line per request (health checks only at DEBUG), with `correlation_id`, method, path, status and `duration_ms`.
- Use `get_logger(__name__)` from `tsg_gateway.observability.logging`. Context values bound with `structlog.contextvars` appear on every line.

## Layout

```
src/tsg_gateway/
  domain/        pure logic, no I/O
  application/   use cases, commands, events, handlers
  ports/         Protocol interfaces
  adapters/      engines, connectors, persistence, storage, messaging, secrets, cache
  entrypoints/   api, azure_functions, aws_lambda, container
  settings.py    environment settings
tests/
  unit/  contract/  integration/  e2e/
```

Layer rules are enforced by `import-linter` (see `[tool.importlinter]` in `pyproject.toml`):
`entrypoints → adapters → application → ports → domain`, and the core never imports web, database or cloud libraries.
