from datetime import UTC, datetime

import httpx

from tests.unit.api.conftest import ACME, BETA

AU_LINE = {
    "currency": "AUD",
    "ship_from": {"country": "AU"},
    "ship_to": {"country": "AU"},
    "lines": [{"tax_category": "TSG-GEN", "unit_price": "100.00"}],
}


async def test_usage_counts_outcomes_and_recent_calculations(client: httpx.AsyncClient) -> None:
    await client.post("/v1/tax/calculate", json=AU_LINE, headers=ACME)
    await client.post("/v1/tax/calculate", json={**AU_LINE, "reference": "SO-2"}, headers=ACME)
    await client.post("/v1/tax/calculate", json={**AU_LINE, "currency": "USD"}, headers=ACME)
    unsupported = {**AU_LINE, "ship_from": {"country": "FR"}, "ship_to": {"country": "FR"}}
    await client.post("/v1/tax/calculate", json={**unsupported, "currency": "EUR"}, headers=ACME)

    summary = (await client.get("/v1/usage/summary", headers=ACME)).json()
    assert summary["month"] == datetime.now(UTC).strftime("%Y-%m")
    assert (summary["requests"], summary["successful"]) == (4, 2)
    assert (summary["rejected"], summary["unsupported"]) == (1, 1)
    assert summary["by_engine"] == [{"engine": "tsg-rules", "requests": 4, "responded": 2}]
    today = next(d for d in summary["by_day"] if d["day"] == datetime.now(UTC).date().isoformat())
    assert today == {"day": today["day"], "requests": 4, "successful": 2}

    recent = (await client.get("/v1/calculations/recent", headers=ACME)).json()
    assert [r["reference"] for r in recent] == ["SO-2", None]
    assert recent[0]["tax_total"] == "10.00"

    beta = (await client.get("/v1/usage/summary", headers=BETA)).json()
    assert beta["requests"] == 0


async def test_usage_summary_for_a_past_month_has_every_day(client: httpx.AsyncClient) -> None:
    summary = (await client.get("/v1/usage/summary?month=2026-02", headers=ACME)).json()

    assert summary["requests"] == 0
    assert len(summary["by_day"]) == 28


async def test_jurisdictions_and_dev_tenants(client: httpx.AsyncClient) -> None:
    jurisdictions = (await client.get("/v1/tax/jurisdictions")).json()
    assert [j["code"] for j in jurisdictions][:2] == ["AU", "NZ"]

    assert (await client.get("/v1/dev/tenants")).json() == ["acme", "beta"]
