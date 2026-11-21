"""Tax calculation, recent calculations, usage, and dev-only helpers."""

import json
from datetime import UTC, datetime
from importlib import resources
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query
from starlette import status

from tsg_gateway.application.calculation import CalculateRequest, CalculateResponse
from tsg_gateway.application.usage import UsageSummary
from tsg_gateway.domain.canonical.tax import JurisdictionInfo
from tsg_gateway.domain.usage import CalculationRecord
from tsg_gateway.entrypoints.api.dependencies import ServicesDep, SettingsDep, TenantDep

router = APIRouter(prefix="/v1", tags=["tax"])


@router.get("/tax/jurisdictions")
async def list_jurisdictions(services: ServicesDep) -> list[JurisdictionInfo]:
    return services.engine.jurisdictions()


@router.post("/tax/calculate")
async def calculate(
    body: CalculateRequest, tenant: TenantDep, services: ServicesDep
) -> CalculateResponse:
    return await services.calculation.calculate(tenant, body)


@router.get("/calculations/recent")
async def recent_calculations(
    tenant: TenantDep,
    services: ServicesDep,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> list[CalculationRecord]:
    return await services.calculation.recent(tenant, limit)


@router.get("/usage/summary")
async def usage_summary(
    tenant: TenantDep,
    services: ServicesDep,
    month: Annotated[str | None, Query(pattern=r"^\d{4}-\d{2}$")] = None,
) -> UsageSummary:
    month = month or datetime.now(UTC).strftime("%Y-%m")
    return await services.usage.month_summary(tenant, month)


@router.get("/dev/tenants", tags=["dev"])
async def dev_tenants(settings: SettingsDep) -> list[str]:
    """Clients selectable in local/test/dev (until OIDC login)."""
    _require_non_production(settings.is_non_production)
    return settings.dev_tenant_ids


@router.get("/dev/scenarios", tags=["dev"])
async def dev_scenarios(settings: SettingsDep) -> list[dict[str, Any]]:
    """Test scenarios from spec/tax-reference/test-scenarios.md, with expected results."""
    _require_non_production(settings.is_non_production)
    text = resources.files("tsg_gateway.samples").joinpath("scenarios.json").read_text("utf-8")
    scenarios: list[dict[str, Any]] = json.loads(text)
    return scenarios


def _require_non_production(allowed: bool) -> None:
    if not allowed:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
