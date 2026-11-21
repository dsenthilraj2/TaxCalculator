.DEFAULT_GOAL := help
BACKEND := backend
UV := uv --directory $(BACKEND)

.PHONY: help setup sync lint format typecheck arch check test test-cov db down clean

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

setup: ## Install Python 3.13, dependencies and pre-commit hooks; create .env.local
	$(UV) python install
	$(UV) sync
	$(UV) run pre-commit install
	@test -f $(BACKEND)/.env.local || cp .env.example $(BACKEND)/.env.local

sync: ## Install/update dependencies from uv.lock
	$(UV) sync

lint: ## Ruff lint and format check
	$(UV) run ruff check .
	$(UV) run ruff format --check .

format: ## Auto-fix lint issues and format code
	$(UV) run ruff check --fix .
	$(UV) run ruff format .

typecheck: ## mypy (strict)
	$(UV) run mypy

arch: ## Layer rules (import-linter)
	$(UV) run lint-imports

check: lint typecheck arch ## All static checks (same as CI)

test: ## Unit + contract tests (no Docker needed)
	$(UV) run pytest -m "not integration and not e2e"

test-cov: ## Tests with coverage report
	$(UV) run pytest -m "not integration and not e2e" --cov --cov-report=term-missing

db: ## Start local MongoDB (needs Docker)
	docker compose up -d mongo

down: ## Stop local containers
	docker compose down

clean: ## Remove caches and local data
	rm -rf $(BACKEND)/.pytest_cache $(BACKEND)/.mypy_cache $(BACKEND)/.ruff_cache $(BACKEND)/.coverage .localdata
	find $(BACKEND) -type d -name __pycache__ -prune -exec rm -rf {} +
