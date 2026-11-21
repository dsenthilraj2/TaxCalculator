from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI

from tsg_gateway.entrypoints.api.app import create_app
from tsg_gateway.observability.logging import LogFormat
from tsg_gateway.settings import AppEnv, Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None, app_env=AppEnv.TEST, log_format=LogFormat.JSON)


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
