"""Structured logging with structlog.

Every log line carries the values bound in the request context (for example
``correlation_id``). Locally logs are human-readable; in the cloud they are JSON.
Standard-library loggers (uvicorn, httpx, ...) are routed through the same pipeline.
"""

import logging
import sys
from enum import StrEnum
from typing import TextIO

import structlog
from structlog.typing import Processor


class LogFormat(StrEnum):
    """Output format for log lines."""

    CONSOLE = "console"
    JSON = "json"


class _StdoutHandler(logging.StreamHandler[TextIO]):
    """Writes to whatever ``sys.stdout`` is at emit time, not at configuration time."""

    @property
    def stream(self) -> TextIO:
        return sys.stdout

    @stream.setter
    def stream(self, _: TextIO) -> None:
        """Ignore assignment: the stream is always the current ``sys.stdout``."""


def configure_logging(level: str = "INFO", fmt: LogFormat = LogFormat.CONSOLE) -> None:
    """Configure structlog and the standard-library root logger.

    Safe to call more than once; the last call wins.
    """
    shared: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]

    renderer: Processor
    if fmt is LogFormat.JSON:
        final: list[Processor] = [structlog.processors.format_exc_info]
        renderer = structlog.processors.JSONRenderer()
    else:
        final = []
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[*shared, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,
    )

    handler = _StdoutHandler()
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                *final,
                renderer,
            ],
        )
    )

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())

    for name in ("uvicorn", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
    # Requests are logged by RequestContextMiddleware, so uvicorn's access log is redundant.
    logging.getLogger("uvicorn.access").disabled = True


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a logger bound to ``name`` (usually ``__name__``)."""
    logger: structlog.stdlib.BoundLogger = structlog.stdlib.get_logger(name)
    return logger
