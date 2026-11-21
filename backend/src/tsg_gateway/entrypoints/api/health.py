"""Liveness (``/health``) and readiness (``/health/ready``) endpoints."""

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from http import HTTPStatus
from typing import Literal

from fastapi import APIRouter, Response
from pydantic import BaseModel

from tsg_gateway.observability.logging import get_logger
from tsg_gateway.settings import Settings

CHECK_TIMEOUT_SECONDS = 2.0
HEALTH_PATHS = frozenset({"/health", "/health/ready"})

logger = get_logger(__name__)


class HealthResponse(BaseModel):
    """Liveness: the process is up and serving requests."""

    status: Literal["ok"]
    service: str
    version: str
    environment: str


class CheckResult(BaseModel):
    """Outcome of one readiness check (for example, the database)."""

    name: str
    ok: bool
    detail: str | None = None


class ReadinessResponse(BaseModel):
    """Readiness: every dependency the app needs is reachable."""

    status: Literal["ready", "not_ready"]
    checks: list[CheckResult]


ReadinessCheck = Callable[[], Awaitable[CheckResult]]


async def _run_check(check: ReadinessCheck) -> CheckResult:
    name = getattr(check, "__name__", "check")
    try:
        async with asyncio.timeout(CHECK_TIMEOUT_SECONDS):
            return await check()
    except TimeoutError:
        logger.warning("readiness.check_timeout", check=name)
        return CheckResult(name=name, ok=False, detail="timed out")
    except Exception as exc:
        logger.warning("readiness.check_failed", check=name, error=type(exc).__name__)
        return CheckResult(name=name, ok=False, detail=type(exc).__name__)


def build_health_router(
    settings: Settings, version: str, checks: Sequence[ReadinessCheck] = ()
) -> APIRouter:
    """Create the health router. Readiness checks are added by later slices (e.g. MongoDB)."""
    router = APIRouter(tags=["health"])

    @router.get("/health")
    async def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            service=settings.service_name,
            version=version,
            environment=settings.app_env.value,
        )

    @router.get(
        "/health/ready",
        responses={HTTPStatus.SERVICE_UNAVAILABLE.value: {"model": ReadinessResponse}},
    )
    async def ready(response: Response) -> ReadinessResponse:
        results = list(await asyncio.gather(*(_run_check(check) for check in checks)))
        is_ready = all(result.ok for result in results)
        if not is_ready:
            response.status_code = HTTPStatus.SERVICE_UNAVAILABLE.value
        return ReadinessResponse(status="ready" if is_ready else "not_ready", checks=results)

    return router
