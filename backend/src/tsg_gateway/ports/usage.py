"""Storage ports for usage counters and recent calculations."""

from datetime import date
from typing import Protocol

from tsg_gateway.domain.usage import CalculationRecord, UsageCount, UsageKey


class UsageRepository(Protocol):
    """Pre-aggregated usage counters."""

    async def increment(self, key: UsageKey, count: int = 1) -> None: ...
    async def counts(self, tenant_id: str, start: date, end: date) -> list[UsageCount]:
        """Counters with ``start <= day < end``."""
        ...


class CalculationRepository(Protocol):
    """Successful calculations, newest first."""

    async def add(self, record: CalculationRecord) -> None: ...
    async def recent(self, tenant_id: str, limit: int) -> list[CalculationRecord]: ...
