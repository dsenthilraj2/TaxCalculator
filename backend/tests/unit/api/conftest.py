from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI

from tests.support.auth import ACME_ADMIN, BETA_ADMIN, test_verifier
from tsg_gateway.bootstrap import memory_services
from tsg_gateway.entrypoints.api.app import create_app
from tsg_gateway.entrypoints.api.health import ReadinessCheck
from tsg_gateway.observability.logging import LogFormat
from tsg_gateway.settings import AppEnv, Settings, Store

# Signed-in client admins (most tests act as these).
ACME = ACME_ADMIN
BETA = BETA_ADMIN


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None, app_env=AppEnv.TEST, log_format=LogFormat.JSON, store=Store.MEMORY
    )


def build_app(settings: Settings, *checks: ReadinessCheck) -> FastAPI:
    """An app with in-memory storage that trusts only test tokens."""
    return create_app(settings, readiness_checks=checks, services=memory_services(test_verifier()))


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return build_app(settings)


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
