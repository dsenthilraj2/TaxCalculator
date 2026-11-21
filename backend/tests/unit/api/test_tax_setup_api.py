import httpx
import pytest

from tests.unit.api.conftest import ACME, BETA
from tsg_gateway.entrypoints.api.app import create_app
from tsg_gateway.settings import AppEnv, Settings

AU_SALE = {
    "currency": "AUD",
    "ship_from": {"country": "AU"},
    "ship_to": {"country": "AU"},
}


async def test_lists_tsg_categories(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/tax-categories")

    assert response.status_code == 200
    codes = [c["code"] for c in response.json()]
    assert codes[0] == "TSG-GEN"
    assert len(codes) == 11


async def test_tenant_header_is_required(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/products")

    assert response.status_code == 401
    assert "X-TSG-Tenant" in response.json()["detail"]


async def test_unknown_tenant_is_forbidden(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/products", headers={"X-TSG-Tenant": "mallory"})

    assert response.status_code == 403


async def test_dev_tenant_header_rejected_in_production(settings: Settings) -> None:
    prod = settings.model_copy(update={"app_env": AppEnv.PROD})
    transport = httpx.ASGITransport(app=create_app(prod))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.get("/v1/products", headers=ACME)).status_code == 401
        assert (await client.get("/v1/dev/scenarios")).status_code == 404


async def test_product_crud_and_effective_category(client: httpx.AsyncClient) -> None:
    created = await client.put(
        "/v1/products/KIDS-COAT-01",
        json={"name": "Kids coat", "group": "Kids clothing"},
        headers=ACME,
    )
    assert created.status_code == 200
    assert created.json()["category_source"] == "default"
    assert created.json()["resolved_category"] == "TSG-GEN"

    await client.put(
        "/v1/product-groups/Kids clothing", json={"tax_category": "TSG-CLOTH-CHILD"}, headers=ACME
    )
    fetched = (await client.get("/v1/products/KIDS-COAT-01", headers=ACME)).json()
    assert fetched["resolved_category"] == "TSG-CLOTH-CHILD"
    assert fetched["category_source"] == "group"

    deleted = await client.delete("/v1/products/KIDS-COAT-01", headers=ACME)
    assert deleted.status_code == 204
    missing = await client.get("/v1/products/KIDS-COAT-01", headers=ACME)
    assert missing.status_code == 404
    assert missing.json()["type"] == "urn:tsg:problem:not-found"


async def test_rejects_unknown_category(client: httpx.AsyncClient) -> None:
    response = await client.put(
        "/v1/products/X1", json={"name": "X", "tax_category": "TSG-NOPE"}, headers=ACME
    )

    assert response.status_code == 422
    assert response.json()["type"] == "urn:tsg:problem:invalid-request"
    assert "TSG-NOPE" in response.json()["detail"]


async def test_import_filter_and_summary(client: httpx.AsyncClient) -> None:
    products = [
        {"sku": "BREAD", "name": "Sourdough", "tax_category": "TSG-FOOD"},
        {"sku": "COAT", "name": "Kids coat", "group": "Kids clothing"},
        {"sku": "LAMP", "name": "Desk lamp"},
    ]
    imported = await client.post("/v1/products/import", json=products, headers=ACME)
    assert imported.json() == {"imported": 3}
    await client.put(
        "/v1/product-groups/Kids clothing", json={"tax_category": "TSG-CLOTH-CHILD"}, headers=ACME
    )

    unmapped = await client.get("/v1/products", params={"status": "unmapped"}, headers=ACME)
    assert [p["sku"] for p in unmapped.json()] == ["LAMP"]
    searched = await client.get("/v1/products", params={"search": "sour"}, headers=ACME)
    assert [p["sku"] for p in searched.json()] == ["BREAD"]

    summary = (await client.get("/v1/tax-setup/summary", headers=ACME)).json()
    assert summary == {
        "products_total": 3,
        "products_by_product": 1,
        "products_by_group": 1,
        "products_by_default": 1,
        "groups_total": 1,
        "default_category": "TSG-GEN",
    }


async def test_import_rejects_duplicate_skus(client: httpx.AsyncClient) -> None:
    products = [{"sku": "A", "name": "One"}, {"sku": "A", "name": "Two"}]

    response = await client.post("/v1/products/import", json=products, headers=ACME)

    assert response.status_code == 422


async def test_clients_never_see_each_others_products(client: httpx.AsyncClient) -> None:
    await client.put("/v1/products/SECRET", json={"name": "Acme only"}, headers=ACME)

    assert (await client.get("/v1/products", headers=BETA)).json() == []
    assert (await client.get("/v1/products/SECRET", headers=BETA)).status_code == 404


async def test_default_category_change(client: httpx.AsyncClient) -> None:
    updated = await client.put(
        "/v1/tax-settings", json={"default_category": "TSG-BOOK"}, headers=ACME
    )
    assert updated.json() == {"default_category": "TSG-BOOK"}

    resolved = await client.post("/v1/tax-categories/resolve", json={"sku": "NEW"}, headers=ACME)
    assert resolved.json() == {"tax_category": "TSG-BOOK", "source": "default"}


@pytest.mark.parametrize(
    ("line", "expected_tax", "expected_source"),
    [
        ({"sku": "BREAD", "unit_price": "20.00"}, "0.00", "product"),
        ({"product_group": "Kids clothing", "unit_price": "100.00"}, "10.00", "group"),
        ({"sku": "UNKNOWN", "unit_price": "100.00"}, "10.00", "default"),
    ],
)
async def test_calculation_uses_product_setup(
    client: httpx.AsyncClient, line: dict[str, str], expected_tax: str, expected_source: str
) -> None:
    await client.put(
        "/v1/products/BREAD", json={"name": "Bread", "tax_category": "TSG-FOOD"}, headers=ACME
    )
    await client.put(
        "/v1/product-groups/Kids clothing", json={"tax_category": "TSG-CLOTH-CHILD"}, headers=ACME
    )

    response = await client.post(
        "/v1/tax/calculate", json={**AU_SALE, "lines": [line]}, headers=ACME
    )

    assert response.status_code == 200, response.text
    result_line = response.json()["lines"][0]
    assert result_line["tax_amount"] == expected_tax
    assert result_line["category_source"] == expected_source
