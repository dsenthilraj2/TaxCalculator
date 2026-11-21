"""RFC 9457 Problem Details responses."""

from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

import structlog
from fastapi.responses import JSONResponse

PROBLEM_JSON = "application/problem+json"


def problem_response(
    status: int,
    *,
    detail: str | None = None,
    errors: list[dict[str, Any]] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    """Build an ``application/problem+json`` response.

    The current correlation ID is included so clients can quote it to support.
    """
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": HTTPStatus(status).phrase,
        "status": status,
    }
    if detail:
        body["detail"] = detail
    correlation_id = structlog.contextvars.get_contextvars().get("correlation_id")
    if correlation_id:
        body["correlationId"] = correlation_id
    if errors:
        body["errors"] = errors
    return JSONResponse(body, status_code=status, media_type=PROBLEM_JSON, headers=headers)
