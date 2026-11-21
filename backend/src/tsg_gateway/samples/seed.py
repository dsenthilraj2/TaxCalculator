"""Load demo data for local development: ``make seed`` (spec/10-local-development.md §8).

Uses the application services (not raw database writes), so it doubles as a smoke test.
Products and mappings are upserted (safe to re-run); sample calculations are added each run.
"""

import asyncio
import json
from importlib import resources

from tsg_gateway.application.calculation import CalculateRequest
from tsg_gateway.bootstrap import build_services
from tsg_gateway.domain.errors import TaxGatewayError
from tsg_gateway.domain.products import Product
from tsg_gateway.settings import get_settings

GROUPS = {
    "acme": {
        "Groceries": "TSG-FOOD",
        "Cafe": "TSG-FOOD-PREP",
        "Kids clothing": "TSG-CLOTH-CHILD",
        "Books": "TSG-BOOK",
        "Pharmacy": "TSG-MED-RX",
        "Wine": "TSG-ALC",
    },
    "beta": {"Groceries": "TSG-FOOD"},
}

PRODUCTS = {
    "acme": [
        Product(sku="BREAD-SOUR", name="Sourdough loaf", group="Groceries"),
        Product(sku="MILK-2L", name="Full cream milk 2L", group="Groceries"),
        Product(sku="APPLE-1KG", name="Apples 1kg", group="Groceries"),
        Product(
            sku="CHOC-BAR",
            name="Chocolate bar",
            group="Groceries",
            tax_category="TSG-GEN",
            description="Confectionery is taxable even in grocery",
        ),
        Product(sku="COFFEE-FLAT", name="Flat white", group="Cafe"),
        Product(sku="SANDWICH-HOT", name="Toasted sandwich", group="Cafe"),
        Product(sku="KIDS-COAT-01", name="Kids winter coat", group="Kids clothing"),
        Product(sku="KIDS-SHOES-02", name="Kids sneakers", group="Kids clothing"),
        Product(sku="BOOK-ATLAS", name="World atlas", group="Books"),
        Product(sku="BOOK-NOVEL", name="Paperback novel", group="Books"),
        Product(sku="RX-ANTIBIOTIC", name="Antibiotic (prescription)", group="Pharmacy"),
        Product(sku="WINE-SHIRAZ", name="Shiraz 750ml", group="Wine"),
        Product(sku="LAMP-DESK", name="LED desk lamp", group="Electronics"),
        Product(sku="HEADPHONES", name="Wireless headphones", group="Electronics"),
        Product(sku="CHAIR-OFFICE", name="Office chair", group="Furniture"),
        Product(sku="TENT-2P", name="Two-person tent", group="Outdoor"),
        Product(sku="NEWS-DAILY", name="Daily newspaper subscription", tax_category="TSG-NEWS"),
        Product(sku="ENERGY-PLAN", name="Home electricity plan", tax_category="TSG-ENERGY-HOME"),
    ],
    "beta": [
        Product(sku="RICE-5KG", name="Rice 5kg", group="Groceries"),
        Product(sku="KETTLE", name="Electric kettle"),
    ],
}


async def seed() -> None:
    """Upsert demo products and mappings, then run the documented scenarios for Acme."""
    settings = get_settings()
    services = build_services(settings)
    await services.start()
    try:
        for tenant, groups in GROUPS.items():
            for group, category in groups.items():
                await services.tax_setup.upsert_group(tenant, group, category)
            count = await services.tax_setup.upsert_products(tenant, PRODUCTS[tenant])
            print(f"{tenant}: {count} products, {len(groups)} group mappings")  # noqa: T201

        text = resources.files("tsg_gateway.samples").joinpath("scenarios.json").read_text()
        succeeded = failed = 0
        for scenario in json.loads(text):
            try:
                request = CalculateRequest.model_validate(scenario["request"])
                await services.calculation.calculate("acme", request)
                succeeded += 1
            except (TaxGatewayError, ValueError):
                failed += 1
        print(f"acme: {succeeded} sample calculations, {failed} rejected (expected)")  # noqa: T201
    finally:
        await services.stop()


def main() -> None:
    """Entry point for ``tsg-seed``."""
    asyncio.run(seed())


if __name__ == "__main__":
    main()
