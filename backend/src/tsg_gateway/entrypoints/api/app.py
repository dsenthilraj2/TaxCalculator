"""FastAPI application factory."""

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from http import HTTPStatus
from importlib.metadata import PackageNotFoundError, version

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from tsg_gateway.bootstrap import Services, build_services
from tsg_gateway.domain.errors import (
    AuthenticationError,
    DependencyUnavailableError,
    NotFoundError,
    PermissionDeniedError,
    TaxGatewayError,
)
from tsg_gateway.entrypoints.api import routes_tax, routes_tax_setup
from tsg_gateway.entrypoints.api.health import HEALTH_PATHS, ReadinessCheck, build_health_router
from tsg_gateway.entrypoints.api.middleware import RequestContextMiddleware
from tsg_gateway.entrypoints.api.problems import problem_response
from tsg_gateway.observability.logging import configure_logging, get_logger
from tsg_gateway.settings import Settings, get_settings

logger = get_logger(__name__)

PROBLEM_TYPE_PREFIX = "urn:tsg:problem:"

_ERROR_STATUS: dict[type[TaxGatewayError], HTTPStatus] = {
    NotFoundError: HTTPStatus.NOT_FOUND,
    AuthenticationError: HTTPStatus.UNAUTHORIZED,
    PermissionDeniedError: HTTPStatus.FORBIDDEN,
    DependencyUnavailableError: HTTPStatus.SERVICE_UNAVAILABLE,
}


def _package_version() -> str:
    try:
        return version("tsg-gateway")
    except PackageNotFoundError:
        return "0.0.0+unknown"


def create_app(
    settings: Settings | None = None,
    readiness_checks: Sequence[ReadinessCheck] = (),
    services: Services | None = None,
) -> FastAPI:
    """Build the API. Used directly by tests and as a uvicorn ``--factory``."""
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.log_format)
    services = services or build_services(settings)
    app_version = _package_version()
    show_docs = settings.is_non_production

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        await services.start()
        try:
            yield
        finally:
            await services.stop()

    app = FastAPI(
        title="TSG Tax Gateway",
        version=app_version,
        docs_url="/docs" if show_docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if show_docs else None,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.services = services

    checks = [*services.readiness_checks, *readiness_checks]
    app.include_router(build_health_router(settings, app_version, checks))
    app.include_router(routes_tax_setup.router)
    app.include_router(routes_tax.router)

    @app.exception_handler(TaxGatewayError)
    async def domain_error(_: Request, exc: TaxGatewayError) -> JSONResponse:
        status_code = _ERROR_STATUS.get(type(exc), HTTPStatus.UNPROCESSABLE_CONTENT)
        headers = (
            {"WWW-Authenticate": 'Bearer error="invalid_token"'}
            if isinstance(exc, AuthenticationError)
            else None
        )
        return problem_response(
            status_code.value,
            detail=exc.message,
            problem_type=PROBLEM_TYPE_PREFIX + exc.code,
            headers=headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        phrase = HTTPStatus(exc.status_code).phrase
        detail = None if exc.detail == phrase else str(exc.detail)
        return problem_response(exc.status_code, detail=detail, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
            for error in exc.errors()
        ]
        return problem_response(
            HTTPStatus.UNPROCESSABLE_CONTENT.value,
            detail="Request validation failed.",
            problem_type=PROBLEM_TYPE_PREFIX + "validation",
            errors=errors,
        )

    app.add_middleware(RequestContextMiddleware, quiet_paths=HEALTH_PATHS)

    logger.info(
        "app.created",
        service=settings.service_name,
        version=app_version,
        environment=settings.app_env.value,
        cloud=settings.cloud.value,
        store=settings.store.value,
    )
    return app
