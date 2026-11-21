import json

import httpx
import pytest
from fastapi import FastAPI

CORRELATION_HEADER = "X-Correlation-Id"


def _log_lines(output: str) -> list[dict[str, object]]:
    return [json.loads(line) for line in output.splitlines() if line.startswith("{")]


async def test_generates_correlation_id_when_missing(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")

    correlation_id = response.headers[CORRELATION_HEADER]
    assert len(correlation_id) == 32


async def test_echoes_valid_incoming_correlation_id(client: httpx.AsyncClient) -> None:
    response = await client.get("/health", headers={CORRELATION_HEADER: "erp-req-123"})

    assert response.headers[CORRELATION_HEADER] == "erp-req-123"


@pytest.mark.parametrize("bad_value", ["has spaces", "x" * 129, "semi;colon"])
async def test_replaces_unsafe_incoming_correlation_id(
    client: httpx.AsyncClient, bad_value: str
) -> None:
    response = await client.get("/health", headers={CORRELATION_HEADER: bad_value})

    assert response.headers[CORRELATION_HEADER] != bad_value


async def test_unknown_route_returns_problem_details(client: httpx.AsyncClient) -> None:
    response = await client.get("/nope", headers={CORRELATION_HEADER: "abc"})

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json() == {
        "type": "about:blank",
        "title": "Not Found",
        "status": 404,
        "correlationId": "abc",
    }


async def test_validation_error_returns_problem_details(app: FastAPI) -> None:
    @app.get("/items/{item_id}")
    async def get_item(item_id: int) -> dict[str, int]:
        return {"id": item_id}

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/items/not-a-number")

    assert response.status_code == 422
    body = response.json()
    assert body["title"] == "Unprocessable Content"
    assert body["errors"][0]["loc"] == ["path", "item_id"]


async def test_unhandled_error_returns_500_and_is_logged(
    app: FastAPI, capsys: pytest.CaptureFixture[str]
) -> None:
    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("secret internal detail")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/boom", headers={CORRELATION_HEADER: "trace-1"})

    assert response.status_code == 500
    assert response.headers[CORRELATION_HEADER] == "trace-1"
    assert response.json()["correlationId"] == "trace-1"
    assert "secret internal detail" not in response.text

    logs = _log_lines(capsys.readouterr().out)
    error = next(line for line in logs if line["event"] == "request.unhandled_error")
    assert error["correlation_id"] == "trace-1"
    assert "RuntimeError" in str(error["exception"])


async def test_logs_one_line_per_request(
    client: httpx.AsyncClient, capsys: pytest.CaptureFixture[str]
) -> None:
    capsys.readouterr()

    await client.get("/nope", headers={CORRELATION_HEADER: "trace-2"})

    completed = [
        line for line in _log_lines(capsys.readouterr().out) if line["event"] == "request.completed"
    ]
    assert len(completed) == 1
    assert completed[0]["correlation_id"] == "trace-2"
    assert completed[0]["method"] == "GET"
    assert completed[0]["path"] == "/nope"
    assert completed[0]["status"] == 404
    assert isinstance(completed[0]["duration_ms"], float)


async def test_health_requests_are_not_logged_at_info(
    client: httpx.AsyncClient, capsys: pytest.CaptureFixture[str]
) -> None:
    capsys.readouterr()

    await client.get("/health")

    events = [line["event"] for line in _log_lines(capsys.readouterr().out)]
    assert "request.completed" not in events
