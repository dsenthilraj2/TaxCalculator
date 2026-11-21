"""Composition root: picks adapters from settings and wires the application services."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

import httpx
from pymongo import AsyncMongoClient

from tsg_gateway.adapters.engines.tsg_rules.engine import TsgRulesEngine
from tsg_gateway.adapters.identity.oidc import ClaimNames, HttpJwksSource, OidcTokenVerifier
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
from tsg_gateway.ports.identity import TokenVerifier
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
    token_verifier: TokenVerifier
    readiness_checks: list[ReadinessCheck] = field(default_factory=list)
    start: Callable[[], Awaitable[None]] = _noop
    stop: Callable[[], Awaitable[None]] = _noop


def build_services(settings: Settings) -> Services:
    """Wire services for the configured store, verifying tokens against the OIDC issuer."""
    http = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
    verifier = OidcTokenVerifier(
        issuer=settings.oidc_issuer,
        audience=settings.oidc_audience,
        jwks=HttpJwksSource(settings.oidc_issuer, http),
        claims=ClaimNames(roles=settings.oidc_roles_claim, tenant=settings.oidc_tenant_claim),
    )

    async def identity_provider() -> CheckResult:
        reachable = await verifier.is_reachable()
        return CheckResult(
            name="identity-provider",
            ok=reachable,
            detail=None if reachable else settings.oidc_issuer,
        )

    services = (
        _mongo_services(settings, verifier)
        if settings.store is Store.MONGO
        else memory_services(verifier)
    )
    services.readiness_checks.append(identity_provider)
    stop_store = services.stop

    async def stop() -> None:
        await stop_store()
        await http.aclose()

    services.stop = stop
    return services


def memory_services(token_verifier: TokenVerifier) -> Services:
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
        token_verifier=token_verifier,
    )


def _mongo_services(settings: Settings, token_verifier: TokenVerifier) -> Services:
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
        token_verifier=token_verifier,
        readiness_checks=[mongodb],
        start=start,
        stop=stop,
    )
