"""FastAPI application factory."""

from collections.abc import Sequence
from http import HTTPStatus
from importlib.metadata import PackageNotFoundError, version

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from tsg_gateway.entrypoints.api.health import HEALTH_PATHS, ReadinessCheck, build_health_router
from tsg_gateway.entrypoints.api.middleware import RequestContextMiddleware
from tsg_gateway.entrypoints.api.problems import problem_response
from tsg_gateway.observability.logging import configure_logging, get_logger
from tsg_gateway.settings import AppEnv, Settings, get_settings

logger = get_logger(__name__)


def _package_version() -> str:
    try:
        return version("tsg-gateway")
    except PackageNotFoundError:
        return "0.0.0+unknown"


def create_app(
    settings: Settings | None = None, readiness_checks: Sequence[ReadinessCheck] = ()
) -> FastAPI:
    """Build the API. Used directly by tests and as a uvicorn ``--factory``."""
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.log_format)
    app_version = _package_version()
    show_docs = settings.app_env in {AppEnv.LOCAL, AppEnv.TEST, AppEnv.DEV}

    app = FastAPI(
        title="TSG Tax Gateway",
        version=app_version,
        docs_url="/docs" if show_docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if show_docs else None,
    )
    app.include_router(build_health_router(settings, app_version, readiness_checks))

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
            errors=errors,
        )

    app.add_middleware(RequestContextMiddleware, quiet_paths=HEALTH_PATHS)

    logger.info(
        "app.created",
        service=settings.service_name,
        version=app_version,
        environment=settings.app_env.value,
        cloud=settings.cloud.value,
    )
    return app
