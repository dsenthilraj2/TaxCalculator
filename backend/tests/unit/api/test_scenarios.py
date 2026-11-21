"""Every scenario in spec/tax-reference/test-scenarios.md, run through the API."""

import json
from importlib import resources
from typing import Any

import httpx
import pytest

from tests.unit.api.conftest import ACME


def _scenarios() -> list[dict[str, Any]]:
    text = resources.files("tsg_gateway.samples").joinpath("scenarios.json").read_text("utf-8")
    scenarios: list[dict[str, Any]] = json.loads(text)
    return scenarios


SCENARIOS = _scenarios()


def test_all_documented_scenarios_are_present() -> None:
    assert len(SCENARIOS) == 40
    assert len({s["id"] for s in SCENARIOS}) == len(SCENARIOS)


@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s["id"] for s in SCENARIOS])
async def test_scenario(client: httpx.AsyncClient, scenario: dict[str, Any]) -> None:
    response = await client.post("/v1/tax/calculate", json=scenario["request"], headers=ACME)

    expected = scenario["expected"]
    assert response.status_code == expected["status"], response.text
    body = response.json()
    if expected["status"] == 200:
        assert body["tax_total"] == expected["tax_total"]
        assert body["gross_total"] == expected["gross_total"]
        assert body["responded_by"] == "tsg-rules"
    else:
        assert body["type"] == expected["problem_type"]


async def test_scenarios_endpoint_serves_the_same_file(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/dev/scenarios")

    assert response.status_code == 200
    assert response.json() == SCENARIOS
