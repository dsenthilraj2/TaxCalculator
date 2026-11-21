"""Rate tables for the simple countries in spec/tax-reference/.

Simplified for testing and demos, not for compliance. Categories marked "verify" in the
reference are deliberately left out, so the engine reports them as unsupported.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum

from tsg_gateway.domain.canonical.tax import Treatment
from tsg_gateway.domain.tax_categories import TAX_CATEGORIES

RULES_VERSION = "2026-11-21"


class Rounding(StrEnum):
    """Rounding method for a jurisdiction (tax-reference README, rule 5)."""

    PER_LINE_HALF_UP = "per_line_half_up"
    PER_RATE_ROUND_DOWN = "per_rate_round_down"


@dataclass(frozen=True)
class Rule:
    """Rate and treatment for one category."""

    rate: Decimal
    treatment: Treatment


@dataclass(frozen=True)
class Jurisdiction:
    """A country (or US state) the simple engine can calculate."""

    code: str
    country: str
    region: str | None
    name: str
    tax_name: str
    currency: str
    rounding: Rounding
    categories: dict[str, Rule] = field(default_factory=dict)
    customer_exemptions: bool = False


def _rule(rate: str, treatment: Treatment) -> Rule:
    return Rule(Decimal(rate), treatment)


def _uniform(rate: str, **overrides: Rule) -> dict[str, Rule]:
    """Every category at ``rate`` (standard), with per-category overrides."""
    table = {category.code: _rule(rate, Treatment.STANDARD) for category in TAX_CATEGORIES}
    table.update({code.replace("_", "-"): rule for code, rule in overrides.items()})
    return table


_STD = Treatment.STANDARD
_ZERO = _rule("0", Treatment.ZERO_RATED)
_EXEMPT = _rule("0", Treatment.EXEMPT)
_GST_FREE = _rule("0", Treatment.GST_FREE)
_NOT_TAXABLE = _rule("0", Treatment.NOT_TAXABLE)


def _us_state(code: str, name: str, rate: str) -> Jurisdiction:
    return Jurisdiction(
        code=f"US-{code}",
        country="US",
        region=code,
        name=f"United States - {name}",
        tax_name="Sales tax",
        currency="USD",
        rounding=Rounding.PER_LINE_HALF_UP,
        customer_exemptions=True,
        categories={
            "TSG-GEN": _rule(rate, _STD),
            "TSG-FOOD": _EXEMPT,
            "TSG-FOOD-PREP": _rule(rate, _STD),
            "TSG-ALC": _rule(rate, _STD),
            "TSG-MED-RX": _EXEMPT,
            "TSG-EDU": _NOT_TAXABLE,
            "TSG-FIN": _NOT_TAXABLE,
            "TSG-CLOTH-CHILD": _rule(rate, _STD),
            "TSG-BOOK": _rule(rate, _STD),
        },
    )


JURISDICTIONS: tuple[Jurisdiction, ...] = (
    Jurisdiction(
        code="AU",
        country="AU",
        region=None,
        name="Australia",
        tax_name="GST",
        currency="AUD",
        rounding=Rounding.PER_LINE_HALF_UP,
        categories=_uniform(
            "0.10",
            TSG_FOOD=_GST_FREE,
            TSG_MED_RX=_GST_FREE,
            TSG_EDU=_GST_FREE,
            TSG_FIN=_rule("0", Treatment.INPUT_TAXED),
        ),
    ),
    Jurisdiction(
        code="NZ",
        country="NZ",
        region=None,
        name="New Zealand",
        tax_name="GST",
        currency="NZD",
        rounding=Rounding.PER_LINE_HALF_UP,
        categories=_uniform("0.15", TSG_FIN=_EXEMPT),
    ),
    Jurisdiction(
        code="SG",
        country="SG",
        region=None,
        name="Singapore",
        tax_name="GST",
        currency="SGD",
        rounding=Rounding.PER_LINE_HALF_UP,
        categories=_uniform("0.09", TSG_FIN=_EXEMPT),
    ),
    Jurisdiction(
        code="JP",
        country="JP",
        region=None,
        name="Japan",
        tax_name="Consumption tax",
        currency="JPY",
        rounding=Rounding.PER_RATE_ROUND_DOWN,
        categories=_uniform(
            "0.10",
            TSG_FOOD=_rule("0.08", Treatment.REDUCED),
            TSG_NEWS=_rule("0.08", Treatment.REDUCED),
            TSG_MED_RX=_EXEMPT,
            TSG_EDU=_EXEMPT,
            TSG_FIN=_EXEMPT,
        ),
    ),
    Jurisdiction(
        code="GB",
        country="GB",
        region=None,
        name="United Kingdom",
        tax_name="VAT",
        currency="GBP",
        rounding=Rounding.PER_LINE_HALF_UP,
        categories=_uniform(
            "0.20",
            TSG_FOOD=_ZERO,
            TSG_MED_RX=_ZERO,
            TSG_EDU=_EXEMPT,
            TSG_FIN=_EXEMPT,
            TSG_CLOTH_CHILD=_ZERO,
            TSG_ENERGY_HOME=_rule("0.05", Treatment.REDUCED),
            TSG_NEWS=_ZERO,
            TSG_BOOK=_ZERO,
        ),
    ),
    _us_state("MI", "Michigan", "0.06"),
    _us_state("IN", "Indiana", "0.07"),
)
