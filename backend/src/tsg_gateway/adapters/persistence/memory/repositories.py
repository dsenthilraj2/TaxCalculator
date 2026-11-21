"""In-memory repositories. Same behaviour as the MongoDB ones (shared contract tests)."""

from collections import defaultdict
from collections.abc import Sequence
from datetime import date

from tsg_gateway.domain.products import GroupMapping, Product, TaxSettings
from tsg_gateway.domain.usage import CalculationRecord, UsageCount, UsageKey


class InMemoryProductRepository:
    def __init__(self) -> None:
        self._items: dict[str, dict[str, Product]] = defaultdict(dict)

    async def get(self, tenant_id: str, sku: str) -> Product | None:
        return self._items[tenant_id].get(sku)

    async def list_all(self, tenant_id: str) -> list[Product]:
        return list(self._items[tenant_id].values())

    async def upsert(self, tenant_id: str, product: Product) -> None:
        self._items[tenant_id][product.sku] = product

    async def upsert_many(self, tenant_id: str, products: Sequence[Product]) -> None:
        for product in products:
            self._items[tenant_id][product.sku] = product

    async def delete(self, tenant_id: str, sku: str) -> bool:
        return self._items[tenant_id].pop(sku, None) is not None


class InMemoryGroupMappingRepository:
    def __init__(self) -> None:
        self._items: dict[str, dict[str, GroupMapping]] = defaultdict(dict)

    async def list_all(self, tenant_id: str) -> list[GroupMapping]:
        return list(self._items[tenant_id].values())

    async def upsert(self, tenant_id: str, mapping: GroupMapping) -> None:
        self._items[tenant_id][mapping.group] = mapping

    async def delete(self, tenant_id: str, group: str) -> bool:
        return self._items[tenant_id].pop(group, None) is not None


class InMemoryTaxSettingsRepository:
    def __init__(self) -> None:
        self._items: dict[str, TaxSettings] = {}

    async def get(self, tenant_id: str) -> TaxSettings | None:
        return self._items.get(tenant_id)

    async def save(self, tenant_id: str, settings: TaxSettings) -> None:
        self._items[tenant_id] = settings


class InMemoryUsageRepository:
    def __init__(self) -> None:
        self._counts: dict[UsageKey, int] = defaultdict(int)

    async def increment(self, key: UsageKey, count: int = 1) -> None:
        self._counts[key] += count

    async def counts(self, tenant_id: str, start: date, end: date) -> list[UsageCount]:
        return [
            UsageCount(key=key, count=count)
            for key, count in self._counts.items()
            if key.tenant_id == tenant_id and start <= key.day < end
        ]


class InMemoryCalculationRepository:
    def __init__(self) -> None:
        self._items: list[CalculationRecord] = []

    async def add(self, record: CalculationRecord) -> None:
        self._items.append(record)

    async def recent(self, tenant_id: str, limit: int) -> list[CalculationRecord]:
        mine = [record for record in self._items if record.tenant_id == tenant_id]
        return sorted(mine, key=lambda record: record.created_at, reverse=True)[:limit]
