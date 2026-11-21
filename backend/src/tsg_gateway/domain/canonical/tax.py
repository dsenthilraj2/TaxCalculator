"""Canonical tax request and result: the only shape engines and the core exchange."""

from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

CountryCode = Annotated[str, StringConstraints(pattern=r"^[A-Za-z]{2}$", to_upper=True)]
CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Za-z]{3}$", to_upper=True)]
RegionCode = Annotated[str, StringConstraints(max_length=10, to_upper=True)]


class Address(BaseModel):
    """A location. Only country (and region for some countries) affects the simple engine."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    country: CountryCode
    region: RegionCode | None = None
    city: str | None = None
    postal_code: str | None = None


class CustomerExemption(StrEnum):
    """Customer-level exemption (US sales tax only)."""

    NONE = "none"
    RESALE = "resale"


class Customer(BaseModel):
    """The buyer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    customer_id: str | None = None
    exemption: CustomerExemption = CustomerExemption.NONE


class Treatment(StrEnum):
    """How a line was taxed."""

    STANDARD = "standard"
    REDUCED = "reduced"
    ZERO_RATED = "zero_rated"
    GST_FREE = "gst_free"
    EXEMPT = "exempt"
    INPUT_TAXED = "input_taxed"
    NOT_TAXABLE = "not_taxable"
    EXPORT = "export"
    EXEMPT_CUSTOMER = "exempt_customer"


class TaxLine(BaseModel):
    """A line with its tax category already resolved."""

    model_config = ConfigDict(frozen=True)

    line_id: str
    tax_category: str
    quantity: Decimal
    unit_price: Decimal


class TaxRequest(BaseModel):
    """Engine input."""

    model_config = ConfigDict(frozen=True)

    currency: str
    prices_include_tax: bool
    ship_from: Address
    ship_to: Address
    customer: Customer
    lines: tuple[TaxLine, ...]


class LineTax(BaseModel):
    """Tax for one line."""

    model_config = ConfigDict(frozen=True)

    line_id: str
    tax_category: str
    treatment: Treatment
    rate: Decimal
    net_amount: Decimal
    tax_amount: Decimal
    gross_amount: Decimal


class TaxResult(BaseModel):
    """Engine output."""

    model_config = ConfigDict(frozen=True)

    engine: str
    rules_version: str
    jurisdiction: str
    jurisdiction_name: str
    tax_name: str
    currency: str
    prices_include_tax: bool
    lines: tuple[LineTax, ...]
    net_total: Decimal
    tax_total: Decimal
    gross_total: Decimal


class CategoryRate(BaseModel):
    """How a jurisdiction treats one tax category."""

    model_config = ConfigDict(frozen=True)

    tax_category: str
    rate: Decimal
    treatment: Treatment


class JurisdictionInfo(BaseModel):
    """A jurisdiction an engine can calculate."""

    model_config = ConfigDict(frozen=True)

    code: str
    country: str
    region: str | None
    name: str
    tax_name: str
    currency: str
    customer_exemptions: bool
    categories: tuple[CategoryRate, ...] = Field(default=())
