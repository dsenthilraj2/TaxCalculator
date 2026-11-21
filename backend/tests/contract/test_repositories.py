"""One test suite, every repository implementation (REQ-DEV-6).

The MongoDB variant needs a running MongoDB (``make db``) and is marked ``integration``.
Set TSG_TEST_MONGO_URI to point elsewhere.
"""

import os
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import pytest
from pymongo import AsyncMongoClient

from tsg_gateway.adapters.persistence.memory.repositories import (
    InMemoryCalculationRepository,
    InMemoryGroupMappingRepository,
    InMemoryProductRepository,
    InMemoryTaxSettingsRepository,
    InMemoryUsageRepository,
)
from tsg_gateway.adapters.persistence.mongo.repositories import (
    MongoCalculationRepository,
    MongoGroupMappingRepository,
    MongoProductRepository,
    MongoTaxSettingsRepository,
    MongoUsageRepository,
    ensure_indexes,
)
from tsg_gateway.domain.products import GroupMapping, Product, TaxSettings
from tsg_gateway.domain.usage import CalculationRecord, UsageAction, UsageKey, UsageOutcome
from tsg_gateway.ports.tax_setup import (
    GroupMappingRepository,
    ProductRepository,
    TaxSettingsRepository,
)
from tsg_gateway.ports.usage import CalculationRepository, UsageRepository

MONGO_URI = os.environ.get(
    "TSG_TEST_MONGO_URI", "mongodb://127.0.0.1:27017/?replicaSet=rs0&directConnection=true"
)


@dataclass
class Repos:
    products: ProductRepository
    groups: GroupMappingRepository
    settings: TaxSettingsRepository
    usage: UsageRepository
    calculations: CalculationRepository


@pytest.fixture(params=["memory", pytest.param("mongo", marks=pytest.mark.integration)])
async def repos(request: pytest.FixtureRequest) -> AsyncIterator[Repos]:
    if request.param == "memory":
        yield Repos(
            InMemoryProductRepository(),
            InMemoryGroupMappingRepository(),
            InMemoryTaxSettingsRepository(),
            InMemoryUsageRepository(),
            InMemoryCalculationRepository(),
        )
        return

    client: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(
        MONGO_URI, tz_aware=True, serverSelectionTimeoutMS=2000
    )
    name = f"tsg_test_{uuid.uuid4().hex[:12]}"
    db = client[name]
    await ensure_indexes(db)
    try:
        yield Repos(
            MongoProductRepository(db),
            MongoGroupMappingRepository(db),
            MongoTaxSettingsRepository(db),
            MongoUsageRepository(db),
            MongoCalculationRepository(db),
        )
    finally:
        await client.drop_database(name)
        await client.close()


async def test_products_upsert_get_list_delete(repos: Repos) -> None:
    lamp = Product(sku="LAMP", name="Desk lamp", group="Lighting")
    await repos.products.upsert("acme", lamp)
    await repos.products.upsert("acme", lamp.model_copy(update={"name": "Lamp v2"}))

    fetched = await repos.products.get("acme", "LAMP")
    assert fetched is not None
    assert fetched.name == "Lamp v2"
    assert fetched.group == "Lighting"
    assert len(await repos.products.list_all("acme")) == 1

    assert await repos.products.delete("acme", "LAMP") is True
    assert await repos.products.delete("acme", "LAMP") is False
    assert await repos.products.get("acme", "LAMP") is None


async def test_products_upsert_many_and_tenant_isolation(repos: Repos) -> None:
    await repos.products.upsert_many(
        "acme", [Product(sku="A", name="A"), Product(sku="B", name="B", tax_category="TSG-FOOD")]
    )
    await repos.products.upsert("beta", Product(sku="A", name="Beta A"))

    assert sorted(p.sku for p in await repos.products.list_all("acme")) == ["A", "B"]
    beta_a = await repos.products.get("beta", "A")
    assert beta_a is not None
    assert beta_a.name == "Beta A"
    assert await repos.products.get("beta", "B") is None


async def test_group_mappings(repos: Repos) -> None:
    await repos.groups.upsert("acme", GroupMapping(group="Kids", tax_category="TSG-CLOTH-CHILD"))
    await repos.groups.upsert("acme", GroupMapping(group="Kids", tax_category="TSG-GEN"))

    expected = [GroupMapping(group="Kids", tax_category="TSG-GEN")]
    assert await repos.groups.list_all("acme") == expected
    assert await repos.groups.list_all("beta") == []
    assert await repos.groups.delete("acme", "Kids") is True
    assert await repos.groups.list_all("acme") == []


async def test_tax_settings(repos: Repos) -> None:
    assert await repos.settings.get("acme") is None

    await repos.settings.save("acme", TaxSettings(default_category="TSG-BOOK"))

    assert await repos.settings.get("acme") == TaxSettings(default_category="TSG-BOOK")
    assert await repos.settings.get("beta") is None


def _key(tenant: str, day: date, outcome: UsageOutcome = UsageOutcome.SUCCESS) -> UsageKey:
    return UsageKey(
        tenant_id=tenant, day=day, action=UsageAction.CALCULATE, engine="tsg-rules", outcome=outcome
    )


async def test_usage_counters_aggregate_and_filter_by_range(repos: Repos) -> None:
    await repos.usage.increment(_key("acme", date(2026, 11, 3)))
    await repos.usage.increment(_key("acme", date(2026, 11, 3)), count=2)
    await repos.usage.increment(_key("acme", date(2026, 11, 3), UsageOutcome.REJECTED))
    await repos.usage.increment(_key("acme", date(2026, 12, 1)))
    await repos.usage.increment(_key("beta", date(2026, 11, 3)))

    counts = await repos.usage.counts("acme", date(2026, 11, 1), date(2026, 12, 1))

    by_outcome = {c.key.outcome: c.count for c in counts}
    assert by_outcome == {UsageOutcome.SUCCESS: 3, UsageOutcome.REJECTED: 1}


async def test_recent_calculations_newest_first(repos: Repos) -> None:
    for minute in (1, 3, 2):
        await repos.calculations.add(
            CalculationRecord(
                id=uuid.uuid4().hex,
                tenant_id="acme",
                created_at=datetime(2026, 11, 21, 10, minute, tzinfo=UTC),
                reference=f"SO-{minute}",
                engine="tsg-rules",
                jurisdiction="AU",
                jurisdiction_name="Australia",
                currency="AUD",
                line_count=1,
                net_total=Decimal("100.00"),
                tax_total=Decimal("10.00"),
                gross_total=Decimal("110.00"),
            )
        )

    recent = await repos.calculations.recent("acme", limit=2)

    assert [r.reference for r in recent] == ["SO-3", "SO-2"]
    assert recent[0].tax_total == Decimal("10.00")
    assert recent[0].created_at.tzinfo is not None
    assert await repos.calculations.recent("beta", limit=5) == []
