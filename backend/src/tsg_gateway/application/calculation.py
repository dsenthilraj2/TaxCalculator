"""Calculate tax: resolve each line's category, ask the engine, record usage."""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from tsg_gateway.application.tax_setup import TaxSetupService
from tsg_gateway.domain.canonical.tax import (
    Address,
    CurrencyCode,
    Customer,
    LineTax,
    TaxLine,
    TaxRequest,
    TaxResult,
)
from tsg_gateway.domain.errors import TaxGatewayError, UnsupportedError
from tsg_gateway.domain.products import CategorySource
from tsg_gateway.domain.usage import CalculationRecord, UsageAction, UsageKey, UsageOutcome
from tsg_gateway.ports.tax_engine import TaxEngine
from tsg_gateway.ports.usage import CalculationRepository, UsageRepository


class CalculateLine(BaseModel):
    """A sale line as sent by a client. Give a SKU, a product group or a tax category."""

    model_config = ConfigDict(extra="forbid")

    line_id: str | None = None
    sku: str | None = None
    product_group: str | None = None
    tax_category: str | None = None
    description: str | None = None
    quantity: Annotated[Decimal, Field(gt=0)] = Decimal(1)
    unit_price: Annotated[Decimal, Field(ge=0)]


class CalculateRequest(BaseModel):
    """Calculate request body (``POST /v1/tax/calculate``)."""

    model_config = ConfigDict(extra="forbid")

    reference: str | None = None
    currency: CurrencyCode
    prices_include_tax: bool = False
    ship_from: Address
    ship_to: Address
    customer: Customer = Customer()
    lines: Annotated[list[CalculateLine], Field(min_length=1, max_length=500)]


class CalculatedLine(LineTax):
    """A result line with where its category came from."""

    sku: str | None
    description: str | None
    category_source: CategorySource


class CalculateResponse(BaseModel):
    """Calculate response body."""

    model_config = ConfigDict(frozen=True)

    calculation_id: str
    reference: str | None
    responded_by: str
    rules_version: str
    jurisdiction: str
    jurisdiction_name: str
    tax_name: str
    currency: str
    prices_include_tax: bool
    lines: list[CalculatedLine]
    net_total: Decimal
    tax_total: Decimal
    gross_total: Decimal


class CalculationService:
    """The calculate use case."""

    def __init__(
        self,
        engine: TaxEngine,
        tax_setup: TaxSetupService,
        usage: UsageRepository,
        calculations: CalculationRepository,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._engine = engine
        self._tax_setup = tax_setup
        self._usage = usage
        self._calculations = calculations
        self._clock = clock

    async def calculate(self, tenant_id: str, request: CalculateRequest) -> CalculateResponse:
        """Calculate and record. Expected errors are counted in usage and re-raised."""
        now = self._clock()
        try:
            response = await self._calculate(tenant_id, request)
        except TaxGatewayError as error:
            outcome = (
                UsageOutcome.UNSUPPORTED
                if isinstance(error, UnsupportedError)
                else UsageOutcome.REJECTED
            )
            await self._count(tenant_id, now, outcome)
            raise
        await self._count(tenant_id, now, UsageOutcome.SUCCESS)
        await self._calculations.add(
            CalculationRecord(
                id=response.calculation_id,
                tenant_id=tenant_id,
                created_at=now,
                reference=response.reference,
                engine=response.responded_by,
                jurisdiction=response.jurisdiction,
                jurisdiction_name=response.jurisdiction_name,
                currency=response.currency,
                line_count=len(response.lines),
                net_total=response.net_total,
                tax_total=response.tax_total,
                gross_total=response.gross_total,
            )
        )
        return response

    async def recent(self, tenant_id: str, limit: int = 10) -> list[CalculationRecord]:
        """Latest successful calculations."""
        return await self._calculations.recent(tenant_id, limit)

    async def _calculate(self, tenant_id: str, request: CalculateRequest) -> CalculateResponse:
        resolver = await self._tax_setup.resolver(tenant_id)
        lines: list[TaxLine] = []
        sources: list[CategorySource] = []
        for index, line in enumerate(request.lines, start=1):
            resolved = await resolver.resolve(
                sku=line.sku, group=line.product_group, line_category=line.tax_category
            )
            lines.append(
                TaxLine(
                    line_id=line.line_id or str(index),
                    tax_category=resolved.tax_category,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                )
            )
            sources.append(resolved.source)

        result: TaxResult = await self._engine.calculate(
            TaxRequest(
                currency=request.currency,
                prices_include_tax=request.prices_include_tax,
                ship_from=request.ship_from,
                ship_to=request.ship_to,
                customer=request.customer,
                lines=tuple(lines),
            )
        )
        return CalculateResponse(
            calculation_id=uuid.uuid4().hex,
            reference=request.reference,
            responded_by=result.engine,
            rules_version=result.rules_version,
            jurisdiction=result.jurisdiction,
            jurisdiction_name=result.jurisdiction_name,
            tax_name=result.tax_name,
            currency=result.currency,
            prices_include_tax=result.prices_include_tax,
            lines=[
                CalculatedLine(
                    **line_tax.model_dump(),
                    sku=source_line.sku,
                    description=source_line.description,
                    category_source=source,
                )
                for line_tax, source_line, source in zip(
                    result.lines, request.lines, sources, strict=True
                )
            ],
            net_total=result.net_total,
            tax_total=result.tax_total,
            gross_total=result.gross_total,
        )

    async def _count(self, tenant_id: str, now: datetime, outcome: UsageOutcome) -> None:
        await self._usage.increment(
            UsageKey(
                tenant_id=tenant_id,
                day=now.date(),
                action=UsageAction.CALCULATE,
                engine=self._engine.engine_id,
                outcome=outcome,
            )
        )
