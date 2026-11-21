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

## Endpoints so far

| Path | Purpose |
|---|---|
| `GET /health` | Liveness: service, version, environment |
| `GET /health/ready` | Readiness: runs dependency checks (none yet). `503` if any check fails or times out (2 s). |
| `GET /docs` | Swagger UI (local/test/dev only) |

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
