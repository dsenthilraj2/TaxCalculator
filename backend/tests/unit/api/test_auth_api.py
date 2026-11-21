"""Authentication and authorization through the API (spec/tax-reference SYS-01..03, SYS-06)."""

import httpx
import pytest

from tests.support.auth import (
    ACME_ADMIN,
    ACME_USER,
    BETA_ADMIN,
    TSG_ADMIN_TOKEN,
    TSG_ANALYST_TOKEN,
    bearer,
    token,
)

PRODUCT = {"name": "Lamp"}


async def test_missing_token_is_401_with_bearer_challenge(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/products")

    assert response.status_code == 401
    assert response.headers["www-authenticate"].startswith("Bearer")
    assert response.json()["type"] == "urn:tsg:problem:unauthenticated"


@pytest.mark.parametrize(
    ("bad_token", "message"),
    [
        (token(["ClientAdmin"], "acme", expires_in=-3600), "expired"),
        (token(["ClientAdmin"], "acme", audience="someone-else"), "not intended for this API"),
        (token(["ClientAdmin"], "acme", issuer="https://evil.example"), "issuer"),
        (token(["ClientAdmin"], "acme", signed_by_other_key=True), "Invalid token"),
        (token(["ClientAdmin"], "acme", kid="unknown"), "unknown key"),
        ("not-a-jwt", "Malformed"),
    ],
    ids=["expired", "wrong-audience", "wrong-issuer", "bad-signature", "unknown-kid", "garbage"],
)
async def test_invalid_tokens_are_rejected(
    client: httpx.AsyncClient, bad_token: str, message: str
) -> None:
    response = await client.get("/v1/products", headers=bearer(bad_token))

    assert response.status_code == 401
    assert message in response.json()["detail"]


async def test_me_describes_the_caller(client: httpx.AsyncClient) -> None:
    acme = (await client.get("/v1/me", headers=ACME_USER)).json()
    assert acme["roles"] == ["ClientUser"]
    assert acme["tenants"] == ["acme"]
    assert acme["can_edit_setup"] is False
    assert acme["is_tsg_staff"] is False

    staff = (await client.get("/v1/me", headers=bearer(TSG_ADMIN_TOKEN))).json()
    assert staff["tenants"] == ["acme", "beta"]
    assert staff["can_edit_setup"] is True
    assert staff["is_tsg_staff"] is True


async def test_client_user_can_read_and_calculate_but_not_edit(client: httpx.AsyncClient) -> None:
    assert (await client.get("/v1/products", headers=ACME_USER)).status_code == 200

    edit = await client.put("/v1/products/LAMP", json=PRODUCT, headers=ACME_USER)
    assert edit.status_code == 403
    assert edit.json()["type"] == "urn:tsg:problem:forbidden"

    calculation = await client.post(
        "/v1/tax/calculate",
        json={
            "currency": "AUD",
            "ship_from": {"country": "AU"},
            "ship_to": {"country": "AU"},
            "lines": [{"tax_category": "TSG-GEN", "unit_price": "10.00"}],
        },
        headers=ACME_USER,
    )
    assert calculation.status_code == 200


async def test_client_cannot_choose_another_client(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/products", headers={**BETA_ADMIN, "X-TSG-Tenant": "acme"})

    assert response.status_code == 403
    assert "own client" in response.json()["detail"]


async def test_staff_must_choose_a_known_client(client: httpx.AsyncClient) -> None:
    missing = await client.get("/v1/products", headers=bearer(TSG_ADMIN_TOKEN))
    assert missing.status_code == 403
    unknown = await client.get("/v1/products", headers=bearer(TSG_ADMIN_TOKEN, tenant="mallory"))
    assert unknown.status_code == 403


async def test_staff_admin_works_across_clients(client: httpx.AsyncClient) -> None:
    await client.put("/v1/products/LAMP", json=PRODUCT, headers=ACME_ADMIN)

    acme = await client.get("/v1/products", headers=bearer(TSG_ADMIN_TOKEN, tenant="acme"))
    beta = await client.get("/v1/products", headers=bearer(TSG_ADMIN_TOKEN, tenant="beta"))
    assert [p["sku"] for p in acme.json()] == ["LAMP"]
    assert beta.json() == []

    edit = await client.put(
        "/v1/products/KETTLE", json={"name": "Kettle"}, headers=bearer(TSG_ADMIN_TOKEN, "beta")
    )
    assert edit.status_code == 200


async def test_staff_analyst_is_read_only(client: httpx.AsyncClient) -> None:
    read = await client.get("/v1/products", headers=bearer(TSG_ANALYST_TOKEN, tenant="acme"))
    assert read.status_code == 200

    edit = await client.put(
        "/v1/products/X", json=PRODUCT, headers=bearer(TSG_ANALYST_TOKEN, "acme")
    )
    assert edit.status_code == 403


async def test_token_without_client_is_forbidden(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/products", headers=bearer(token(["ClientAdmin"], None)))

    assert response.status_code == 403
    assert "not linked to a client" in response.json()["detail"]


async def test_reference_data_needs_no_token(client: httpx.AsyncClient) -> None:
    assert (await client.get("/v1/tax-categories")).status_code == 200
    assert (await client.get("/v1/tax/jurisdictions")).status_code == 200
