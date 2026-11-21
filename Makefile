.DEFAULT_GOAL := help
BACKEND := backend
UV := uv --directory $(BACKEND)

.PHONY: help setup sync run idp token seed lint format typecheck arch check test test-cov test-int db db-stop db-docker down clean openapi web-install web web-check demo demo-stop

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

setup: ## Install Python 3.13, dependencies and pre-commit hooks; create .env.local
	$(UV) python install
	$(UV) sync
	$(UV) run pre-commit install
	@test -f $(BACKEND)/.env.local || cp .env.example $(BACKEND)/.env.local

sync: ## Install/update dependencies from uv.lock
	$(UV) sync

run: ## Run the API locally with reload (http://127.0.0.1:8000/docs)
	$(UV) run tsg-api

idp: ## Run the dev identity provider (http://127.0.0.1:8081)
	$(UV) run dev-idp serve

token: ## Print a test access token: make token PERSONA=admin@acme.dev.local
	@$(UV) run dev-idp token --persona $(or $(PERSONA),admin@acme.dev.local)

seed: db ## Load demo products, group mappings and sample calculations
	$(UV) run tsg-seed

lint: ## Ruff lint and format check
	$(UV) run ruff check . ../tools/dev-idp
	$(UV) run ruff format --check . ../tools/dev-idp

format: ## Auto-fix lint issues and format code
	$(UV) run ruff check --fix . ../tools/dev-idp
	$(UV) run ruff format . ../tools/dev-idp

typecheck: ## mypy (strict)
	$(UV) run mypy

arch: ## Layer rules (import-linter)
	$(UV) run lint-imports

check: lint typecheck arch ## All static checks (same as CI)

test: ## Unit + contract tests (no Docker needed)
	$(UV) run pytest -m "not integration and not e2e"

test-cov: ## Tests with coverage report
	$(UV) run pytest -m "not integration and not e2e" --cov --cov-report=term-missing

test-int: db ## All tests including MongoDB integration tests
	$(UV) run pytest -m "not e2e"

db: ## Start local MongoDB (downloads it on first run, no Docker/sudo needed)
	scripts/mongodb.sh start

db-stop: ## Stop local MongoDB
	scripts/mongodb.sh stop

db-docker: ## Alternative: MongoDB in Docker
	docker compose up -d mongo

down: ## Stop Docker containers
	docker compose down

clean: ## Remove caches and local data
	rm -rf $(BACKEND)/.pytest_cache $(BACKEND)/.mypy_cache $(BACKEND)/.ruff_cache $(BACKEND)/.coverage .localdata
	find $(BACKEND) -type d -name __pycache__ -prune -exec rm -rf {} +

openapi: ## Export the OpenAPI spec and regenerate the UI's typed API client
	$(UV) run python -c "import json; from tsg_gateway.entrypoints.api.app import create_app; from tsg_gateway.settings import Settings, Store; print(json.dumps(create_app(Settings(_env_file=None, store=Store.MEMORY, log_level='WARNING')).openapi(), indent=2))" > $(BACKEND)/openapi.json
	cd web/portal && npx openapi-typescript ../../$(BACKEND)/openapi.json -o src/api/schema.d.ts

web-install: ## Install UI dependencies
	cd web/portal && npm ci

web: ## Run the UI dev server (http://127.0.0.1:5173), proxies /v1 to the API
	cd web/portal && npm run dev

web-check: ## Type-check, lint and test the UI
	cd web/portal && npx tsc -b && npm run lint && npx vitest run

demo: ## Start MongoDB + API + UI for a demo (scripts/demo.sh start)
	scripts/demo.sh start

demo-stop: ## Stop the demo, including MongoDB
	scripts/demo.sh stop
