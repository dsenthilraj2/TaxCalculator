import asyncio

import httpx
import pytest

from tsg_gateway.entrypoints.api import health
from tsg_gateway.entrypoints.api.app import create_app
from tsg_gateway.entrypoints.api.health import CheckResult
from tsg_gateway.settings import AppEnv, Settings


async def test_health_reports_service_details(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "tsg-gateway"
    assert body["environment"] == "test"
    assert body["version"]


async def test_ready_with_no_checks_is_ready(client: httpx.AsyncClient) -> None:
    response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": []}


async def _database_ok() -> CheckResult:
    return CheckResult(name="database", ok=True)


async def _database_down() -> CheckResult:
    raise ConnectionError


async def _database_slow() -> CheckResult:
    await asyncio.sleep(1)
    return CheckResult(name="database", ok=True)


async def _get_ready(settings: Settings, *checks: health.ReadinessCheck) -> httpx.Response:
    app = create_app(settings, readiness_checks=checks)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get("/health/ready")


async def test_ready_when_all_checks_pass(settings: Settings) -> None:
    response = await _get_ready(settings, _database_ok)

    assert response.status_code == 200
    assert response.json()["checks"] == [{"name": "database", "ok": True, "detail": None}]


async def test_not_ready_when_a_check_raises(settings: Settings) -> None:
    response = await _get_ready(settings, _database_ok, _database_down)

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["checks"][1] == {"name": "_database_down", "ok": False, "detail": "ConnectionError"}


async def test_not_ready_when_a_check_times_out(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(health, "CHECK_TIMEOUT_SECONDS", 0.01)

    response = await _get_ready(settings, _database_slow)

    assert response.status_code == 503
    assert response.json()["checks"][0]["detail"] == "timed out"


async def test_docs_hidden_in_prod(settings: Settings) -> None:
    prod = settings.model_copy(update={"app_env": AppEnv.PROD})
    transport = httpx.ASGITransport(app=create_app(prod))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.get("/docs")).status_code == 404
        assert (await client.get("/openapi.json")).status_code == 404
