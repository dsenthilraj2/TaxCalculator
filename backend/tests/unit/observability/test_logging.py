import json
import logging

import pytest
import structlog

from tsg_gateway.observability.logging import LogFormat, configure_logging, get_logger


def test_json_format_includes_context_and_standard_fields(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging("INFO", LogFormat.JSON)
    structlog.contextvars.bind_contextvars(correlation_id="c-1")
    try:
        get_logger("tests.logging").info("calculation.done", tenant_id="acme")
    finally:
        structlog.contextvars.clear_contextvars()

    line = json.loads(capsys.readouterr().out.strip())
    assert line["event"] == "calculation.done"
    assert line["tenant_id"] == "acme"
    assert line["correlation_id"] == "c-1"
    assert line["level"] == "info"
    assert line["logger"] == "tests.logging"
    assert line["timestamp"].endswith("Z")


def test_standard_library_loggers_use_the_same_format(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging("INFO", LogFormat.JSON)

    logging.getLogger("uvicorn.error").info("server started")

    line = json.loads(capsys.readouterr().out.strip())
    assert line["event"] == "server started"
    assert line["logger"] == "uvicorn.error"


def test_level_filters_lower_messages(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("WARNING", LogFormat.JSON)

    get_logger("tests.logging").info("hidden")
    get_logger("tests.logging").warning("shown")

    output = capsys.readouterr().out
    assert "hidden" not in output
    assert "shown" in output


def test_console_format_is_human_readable(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO", LogFormat.CONSOLE)

    get_logger("tests.logging").info("readable.event", country="AU")

    output = capsys.readouterr().out
    assert "readable.event" in output
    assert "country" in output
    assert not output.lstrip().startswith("{")
