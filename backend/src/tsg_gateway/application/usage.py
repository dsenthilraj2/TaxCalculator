"""Usage summary for a month: requests, outcomes, which engine responded, per day."""

import calendar
from datetime import date

from pydantic import BaseModel, ConfigDict

from tsg_gateway.domain.errors import InvalidRequestError
from tsg_gateway.domain.usage import UsageOutcome
from tsg_gateway.ports.usage import UsageRepository


class EngineUsage(BaseModel):
    """Requests handled by one engine."""

    model_config = ConfigDict(frozen=True)

    engine: str
    requests: int
    responded: int


class DailyUsage(BaseModel):
    """Requests on one day."""

    model_config = ConfigDict(frozen=True)

    day: date
    requests: int
    successful: int


class UsageSummary(BaseModel):
    """One month of usage for a client."""

    model_config = ConfigDict(frozen=True)

    month: str
    requests: int
    successful: int
    rejected: int
    unsupported: int
    by_engine: list[EngineUsage]
    by_day: list[DailyUsage]


class UsageService:
    """Reads usage counters."""

    def __init__(self, usage: UsageRepository) -> None:
        self._usage = usage

    async def month_summary(self, tenant_id: str, month: str) -> UsageSummary:
        """Summary for ``month`` (``YYYY-MM``), with every day of the month present."""
        try:
            year, month_number = (int(part) for part in month.split("-"))
            start = date(year, month_number, 1)
        except ValueError as exc:
            raise InvalidRequestError("Month must be in the form YYYY-MM.") from exc
        days_in_month = calendar.monthrange(year, month_number)[1]
        end = date(year + month_number // 12, month_number % 12 + 1, 1)

        counts = await self._usage.counts(tenant_id, start, end)
        by_outcome = dict.fromkeys(UsageOutcome, 0)
        engines: dict[str, list[int]] = {}
        days = {date(year, month_number, d): [0, 0] for d in range(1, days_in_month + 1)}
        for item in counts:
            key = item.key
            by_outcome[key.outcome] += item.count
            requests, responded = engines.setdefault(key.engine, [0, 0])
            succeeded = item.count if key.outcome is UsageOutcome.SUCCESS else 0
            engines[key.engine] = [requests + item.count, responded + succeeded]
            days[key.day][0] += item.count
            days[key.day][1] += succeeded

        return UsageSummary(
            month=f"{year:04d}-{month_number:02d}",
            requests=sum(by_outcome.values()),
            successful=by_outcome[UsageOutcome.SUCCESS],
            rejected=by_outcome[UsageOutcome.REJECTED],
            unsupported=by_outcome[UsageOutcome.UNSUPPORTED],
            by_engine=[
                EngineUsage(engine=engine, requests=totals[0], responded=totals[1])
                for engine, totals in sorted(engines.items())
            ],
            by_day=[
                DailyUsage(day=day, requests=values[0], successful=values[1])
                for day, values in days.items()
            ],
        )
