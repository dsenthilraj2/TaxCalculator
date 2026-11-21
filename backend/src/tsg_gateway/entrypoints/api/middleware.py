"""Request context middleware: correlation ID, request logging, last-resort errors."""

import re
import time
import uuid
from http import HTTPStatus

import structlog
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from tsg_gateway.entrypoints.api.problems import problem_response
from tsg_gateway.observability.logging import get_logger

CORRELATION_HEADER = "X-Correlation-Id"
_VALID_CORRELATION_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")

logger = get_logger(__name__)


def _correlation_id_from(scope: Scope) -> str:
    """Reuse the caller's correlation ID when it is safe, otherwise create one."""
    incoming = Headers(scope=scope).get(CORRELATION_HEADER)
    if incoming and _VALID_CORRELATION_ID.fullmatch(incoming):
        return incoming
    return uuid.uuid4().hex


class RequestContextMiddleware:
    """Pure ASGI middleware that wraps every HTTP request.

    - binds ``correlation_id`` to the logging context and echoes it in the response header,
    - logs one ``request.completed`` line per request (``quiet_paths`` at DEBUG level),
    - turns an unhandled exception into a logged 500 Problem Details response.
    """

    def __init__(self, app: ASGIApp, *, quiet_paths: frozenset[str] = frozenset()) -> None:
        self._app = app
        self._quiet_paths = quiet_paths

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        correlation_id = _correlation_id_from(scope)
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        started = time.perf_counter()
        status_code = HTTPStatus.INTERNAL_SERVER_ERROR.value
        response_started = False

        async def send_with_context(message: Message) -> None:
            nonlocal status_code, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]
                MutableHeaders(scope=message)[CORRELATION_HEADER] = correlation_id
            await send(message)

        try:
            await self._app(scope, receive, send_with_context)
        except Exception:
            logger.exception("request.unhandled_error")
            if response_started:
                raise
            response = problem_response(HTTPStatus.INTERNAL_SERVER_ERROR.value)
            await response(scope, receive, send_with_context)
        finally:
            path: str = scope["path"]
            log = logger.debug if path in self._quiet_paths else logger.info
            log(
                "request.completed",
                method=scope["method"],
                path=path,
                status=status_code,
                duration_ms=round((time.perf_counter() - started) * 1000, 2),
            )
            structlog.contextvars.clear_contextvars()
