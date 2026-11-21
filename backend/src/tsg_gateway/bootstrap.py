"""Composition root: picks adapters from settings and wires the application services."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from pymongo import AsyncMongoClient

from tsg_gateway.adapters.engines.tsg_rules.engine import TsgRulesEngine
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
from tsg_gateway.application.calculation import CalculationService
from tsg_gateway.application.tax_setup import TaxSetupService
from tsg_gateway.application.usage import UsageService
from tsg_gateway.entrypoints.api.health import CheckResult, ReadinessCheck
from tsg_gateway.ports.tax_engine import TaxEngine
from tsg_gateway.settings import Settings, Store


async def _noop() -> None:
    return None


@dataclass
class Services:
    """Application services plus start/stop hooks for their infrastructure."""

    tax_setup: TaxSetupService
    calculation: CalculationService
    usage: UsageService
    engine: TaxEngine
    readiness_checks: list[ReadinessCheck] = field(default_factory=list)
    start: Callable[[], Awaitable[None]] = _noop
    stop: Callable[[], Awaitable[None]] = _noop


def build_services(settings: Settings) -> Services:
    """Wire services for the configured store."""
    if settings.store is Store.MONGO:
        return _mongo_services(settings)
    return memory_services()


def memory_services() -> Services:
    """Services backed by in-memory repositories (unit tests, quick demos)."""
    engine = TsgRulesEngine()
    tax_setup = TaxSetupService(
        InMemoryProductRepository(),
        InMemoryGroupMappingRepository(),
        InMemoryTaxSettingsRepository(),
    )
    usage = InMemoryUsageRepository()
    return Services(
        tax_setup=tax_setup,
        calculation=CalculationService(engine, tax_setup, usage, InMemoryCalculationRepository()),
        usage=UsageService(usage),
        engine=engine,
    )


def _mongo_services(settings: Settings) -> Services:
    client: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(
        settings.mongo_uri, tz_aware=True, serverSelectionTimeoutMS=3000
    )
    db = client[settings.mongo_database]
    engine = TsgRulesEngine()
    tax_setup = TaxSetupService(
        MongoProductRepository(db), MongoGroupMappingRepository(db), MongoTaxSettingsRepository(db)
    )
    usage = MongoUsageRepository(db)

    async def mongodb() -> CheckResult:
        await client.admin.command("ping")
        return CheckResult(name="mongodb", ok=True)

    async def start() -> None:
        await ensure_indexes(db)

    async def stop() -> None:
        await client.close()

    return Services(
        tax_setup=tax_setup,
        calculation=CalculationService(engine, tax_setup, usage, MongoCalculationRepository(db)),
        usage=UsageService(usage),
        engine=engine,
        readiness_checks=[mongodb],
        start=start,
        stop=stop,
    )
