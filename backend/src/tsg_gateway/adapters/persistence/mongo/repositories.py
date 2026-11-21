"""MongoDB repositories (MongoDB API: local MongoDB, Cosmos DB for MongoDB, Atlas).

Every document carries ``tenantId`` and every query filters on it (REQ-ARC-2).
Money is stored as decimal strings, never floats.
"""

from collections.abc import Sequence
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from pymongo import ASCENDING, DESCENDING, ReplaceOne
from pymongo.asynchronous.database import AsyncDatabase

from tsg_gateway.domain.products import GroupMapping, Product, TaxSettings
from tsg_gateway.domain.usage import (
    CalculationRecord,
    UsageAction,
    UsageCount,
    UsageKey,
    UsageOutcome,
)

Document = dict[str, Any]

PRODUCTS = "products"
PRODUCT_GROUPS = "product_groups"
TAX_SETTINGS = "tax_settings"
USAGE_COUNTERS = "usage_counters"
CALCULATIONS = "calculations"


async def ensure_indexes(db: AsyncDatabase[Document]) -> None:
    """Create indexes. Idempotent; safe on every start-up."""
    await db[PRODUCTS].create_index([("tenantId", ASCENDING), ("sku", ASCENDING)], unique=True)
    await db[PRODUCT_GROUPS].create_index(
        [("tenantId", ASCENDING), ("group", ASCENDING)], unique=True
    )
    await db[TAX_SETTINGS].create_index([("tenantId", ASCENDING)], unique=True)
    await db[USAGE_COUNTERS].create_index(
        [
            ("tenantId", ASCENDING),
            ("day", ASCENDING),
            ("action", ASCENDING),
            ("engine", ASCENDING),
            ("outcome", ASCENDING),
        ],
        unique=True,
    )
    await db[CALCULATIONS].create_index([("tenantId", ASCENDING), ("createdAt", DESCENDING)])


def _product_doc(tenant_id: str, product: Product) -> Document:
    return {
        "tenantId": tenant_id,
        "sku": product.sku,
        "name": product.name,
        "group": product.group,
        "taxCategory": product.tax_category,
        "description": product.description,
        "schemaVersion": 1,
        "updatedAt": datetime.now(UTC),
    }


def _product(doc: Document) -> Product:
    return Product(
        sku=doc["sku"],
        name=doc["name"],
        group=doc.get("group"),
        tax_category=doc.get("taxCategory"),
        description=doc.get("description"),
    )


class MongoProductRepository:
    def __init__(self, db: AsyncDatabase[Document]) -> None:
        self._collection = db[PRODUCTS]

    async def get(self, tenant_id: str, sku: str) -> Product | None:
        doc = await self._collection.find_one({"tenantId": tenant_id, "sku": sku})
        return _product(doc) if doc else None

    async def list_all(self, tenant_id: str) -> list[Product]:
        return [_product(doc) async for doc in self._collection.find({"tenantId": tenant_id})]

    async def upsert(self, tenant_id: str, product: Product) -> None:
        await self._collection.replace_one(
            {"tenantId": tenant_id, "sku": product.sku},
            _product_doc(tenant_id, product),
            upsert=True,
        )

    async def upsert_many(self, tenant_id: str, products: Sequence[Product]) -> None:
        if not products:
            return
        await self._collection.bulk_write(
            [
                ReplaceOne(
                    {"tenantId": tenant_id, "sku": product.sku},
                    _product_doc(tenant_id, product),
                    upsert=True,
                )
                for product in products
            ]
        )

    async def delete(self, tenant_id: str, sku: str) -> bool:
        result = await self._collection.delete_one({"tenantId": tenant_id, "sku": sku})
        return result.deleted_count == 1


class MongoGroupMappingRepository:
    def __init__(self, db: AsyncDatabase[Document]) -> None:
        self._collection = db[PRODUCT_GROUPS]

    async def list_all(self, tenant_id: str) -> list[GroupMapping]:
        return [
            GroupMapping(group=doc["group"], tax_category=doc["taxCategory"])
            async for doc in self._collection.find({"tenantId": tenant_id})
        ]

    async def upsert(self, tenant_id: str, mapping: GroupMapping) -> None:
        await self._collection.replace_one(
            {"tenantId": tenant_id, "group": mapping.group},
            {
                "tenantId": tenant_id,
                "group": mapping.group,
                "taxCategory": mapping.tax_category,
                "schemaVersion": 1,
                "updatedAt": datetime.now(UTC),
            },
            upsert=True,
        )

    async def delete(self, tenant_id: str, group: str) -> bool:
        result = await self._collection.delete_one({"tenantId": tenant_id, "group": group})
        return result.deleted_count == 1


class MongoTaxSettingsRepository:
    def __init__(self, db: AsyncDatabase[Document]) -> None:
        self._collection = db[TAX_SETTINGS]

    async def get(self, tenant_id: str) -> TaxSettings | None:
        doc = await self._collection.find_one({"tenantId": tenant_id})
        return TaxSettings(default_category=doc["defaultCategory"]) if doc else None

    async def save(self, tenant_id: str, settings: TaxSettings) -> None:
        await self._collection.replace_one(
            {"tenantId": tenant_id},
            {
                "tenantId": tenant_id,
                "defaultCategory": settings.default_category,
                "schemaVersion": 1,
                "updatedAt": datetime.now(UTC),
            },
            upsert=True,
        )


class MongoUsageRepository:
    def __init__(self, db: AsyncDatabase[Document]) -> None:
        self._collection = db[USAGE_COUNTERS]

    async def increment(self, key: UsageKey, count: int = 1) -> None:
        await self._collection.update_one(
            {
                "tenantId": key.tenant_id,
                "day": key.day.isoformat(),
                "action": key.action.value,
                "engine": key.engine,
                "outcome": key.outcome.value,
            },
            {"$inc": {"count": count}},
            upsert=True,
        )

    async def counts(self, tenant_id: str, start: date, end: date) -> list[UsageCount]:
        cursor = self._collection.find(
            {"tenantId": tenant_id, "day": {"$gte": start.isoformat(), "$lt": end.isoformat()}}
        )
        return [
            UsageCount(
                key=UsageKey(
                    tenant_id=doc["tenantId"],
                    day=date.fromisoformat(doc["day"]),
                    action=UsageAction(doc["action"]),
                    engine=doc["engine"],
                    outcome=UsageOutcome(doc["outcome"]),
                ),
                count=doc["count"],
            )
            async for doc in cursor
        ]


class MongoCalculationRepository:
    def __init__(self, db: AsyncDatabase[Document]) -> None:
        self._collection = db[CALCULATIONS]

    async def add(self, record: CalculationRecord) -> None:
        await self._collection.insert_one(
            {
                "_id": record.id,
                "tenantId": record.tenant_id,
                "createdAt": record.created_at,
                "reference": record.reference,
                "engine": record.engine,
                "jurisdiction": record.jurisdiction,
                "jurisdictionName": record.jurisdiction_name,
                "currency": record.currency,
                "lineCount": record.line_count,
                "netTotal": str(record.net_total),
                "taxTotal": str(record.tax_total),
                "grossTotal": str(record.gross_total),
                "schemaVersion": 1,
            }
        )

    async def recent(self, tenant_id: str, limit: int) -> list[CalculationRecord]:
        cursor = (
            self._collection.find({"tenantId": tenant_id})
            .sort("createdAt", DESCENDING)
            .limit(limit)
        )
        return [
            CalculationRecord(
                id=doc["_id"],
                tenant_id=doc["tenantId"],
                created_at=doc["createdAt"].replace(tzinfo=UTC),
                reference=doc.get("reference"),
                engine=doc["engine"],
                jurisdiction=doc["jurisdiction"],
                jurisdiction_name=doc["jurisdictionName"],
                currency=doc["currency"],
                line_count=doc["lineCount"],
                net_total=Decimal(doc["netTotal"]),
                tax_total=Decimal(doc["taxTotal"]),
                gross_total=Decimal(doc["grossTotal"]),
            )
            async for doc in cursor
        ]
