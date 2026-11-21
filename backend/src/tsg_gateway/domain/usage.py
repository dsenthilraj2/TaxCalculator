"""Usage metering: what was asked, which engine answered, and the outcome (spec/11)."""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class UsageAction(StrEnum):
    """The action a request asked for."""

    CALCULATE = "calculate"


class UsageOutcome(StrEnum):
    """How a request ended."""

    SUCCESS = "success"
    REJECTED = "rejected"
    UNSUPPORTED = "unsupported"


class UsageKey(BaseModel):
    """Counter dimensions (one counter per combination per day)."""

    model_config = ConfigDict(frozen=True)

    tenant_id: str
    day: date
    action: UsageAction
    engine: str
    outcome: UsageOutcome


class UsageCount(BaseModel):
    """A counter value."""

    model_config = ConfigDict(frozen=True)

    key: UsageKey
    count: int


class CalculationRecord(BaseModel):
    """A successful calculation, kept for the recent-activity list."""

    model_config = ConfigDict(frozen=True)

    id: str
    tenant_id: str
    created_at: datetime
    reference: str | None
    engine: str
    jurisdiction: str
    jurisdiction_name: str
    currency: str
    line_count: int
    net_total: Decimal
    tax_total: Decimal
    gross_total: Decimal
