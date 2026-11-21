"""Tax engine port: implemented by provider adapters and TSG's own engines."""

from typing import Protocol

from tsg_gateway.domain.canonical.tax import JurisdictionInfo, TaxRequest, TaxResult


class TaxEngine(Protocol):
    """Calculates tax for a canonical request."""

    @property
    def engine_id(self) -> str: ...

    def jurisdictions(self) -> list[JurisdictionInfo]: ...

    async def calculate(self, request: TaxRequest) -> TaxResult: ...
