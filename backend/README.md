# TSG Tax Gateway — Backend

Python 3.13 · FastAPI · Pydantic v2 · hexagonal (ports and adapters) layout.
The design is in [../spec/08-architecture.md](../spec/08-architecture.md) and [../spec/10-local-development.md](../spec/10-local-development.md).

## Quick start

```bash
make setup    # from the repo root: installs Python 3.13 via uv, dependencies, pre-commit hooks
make check    # ruff, mypy, import-linter
make test     # unit + contract tests (no Docker needed)
```

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
