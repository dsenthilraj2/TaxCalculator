"""TSG rules engine: TSG's own calculator for the simple countries (spec/tax-reference/)."""

from collections import defaultdict
from decimal import Decimal

from tsg_gateway.adapters.engines.tsg_rules.rules import (
    JURISDICTIONS,
    RULES_VERSION,
    Jurisdiction,
    Rounding,
    Rule,
)
from tsg_gateway.domain.canonical.tax import (
    CategoryRate,
    CustomerExemption,
    JurisdictionInfo,
    LineTax,
    TaxRequest,
    TaxResult,
    Treatment,
)
from tsg_gateway.domain.errors import InvalidRequestError, UnsupportedError
from tsg_gateway.domain.money import currency_decimals, round_down, round_half_up

ENGINE_ID = "tsg-rules"

_BY_CODE = {jurisdiction.code: jurisdiction for jurisdiction in JURISDICTIONS}
_GST_VAT_COUNTRIES = frozenset(j.country for j in JURISDICTIONS if j.region is None)
_EXPORT = Rule(Decimal(0), Treatment.EXPORT)
_EXEMPT_CUSTOMER = Rule(Decimal(0), Treatment.EXEMPT_CUSTOMER)


class TsgRulesEngine:
    """Deterministic calculator for AU, NZ, SG, JP, GB and US-MI/US-IN."""

    @property
    def engine_id(self) -> str:
        return ENGINE_ID

    def jurisdictions(self) -> list[JurisdictionInfo]:
        return [
            JurisdictionInfo(
                code=j.code,
                country=j.country,
                region=j.region,
                name=j.name,
                tax_name=j.tax_name,
                currency=j.currency,
                customer_exemptions=j.customer_exemptions,
                categories=tuple(
                    CategoryRate(tax_category=code, rate=rule.rate, treatment=rule.treatment)
                    for code, rule in j.categories.items()
                ),
            )
            for j in JURISDICTIONS
        ]

    async def calculate(self, request: TaxRequest) -> TaxResult:
        jurisdiction, is_export = _jurisdiction_for(request)
        if request.currency != jurisdiction.currency:
            raise InvalidRequestError(
                f"Currency {request.currency} does not match {jurisdiction.name} "
                f"({jurisdiction.currency})."
            )
        decimals = currency_decimals(jurisdiction.currency)

        rules: list[Rule] = []
        amounts: list[Decimal] = []
        for line in request.lines:
            rule = jurisdiction.categories.get(line.tax_category)
            if rule is None:
                raise UnsupportedError(
                    f"Tax category {line.tax_category} (line {line.line_id}) is not supported "
                    f"for {jurisdiction.name} by the simple engine."
                )
            if is_export:
                rule = _EXPORT
            elif (
                jurisdiction.customer_exemptions
                and request.customer.exemption is CustomerExemption.RESALE
            ):
                rule = _EXEMPT_CUSTOMER
            rules.append(rule)
            amounts.append(round_half_up(line.quantity * line.unit_price, decimals))

        unrounded = [
            _tax_on(amount, rule.rate, request.prices_include_tax)
            for amount, rule in zip(amounts, rules, strict=True)
        ]
        if jurisdiction.rounding is Rounding.PER_RATE_ROUND_DOWN:
            taxes = _round_down_per_rate(unrounded, rules, decimals)
        else:
            taxes = [round_half_up(value, decimals) for value in unrounded]

        lines = []
        for line, rule, amount, tax in zip(request.lines, rules, amounts, taxes, strict=True):
            net = amount - tax if request.prices_include_tax else amount
            lines.append(
                LineTax(
                    line_id=line.line_id,
                    tax_category=line.tax_category,
                    treatment=rule.treatment,
                    rate=rule.rate,
                    net_amount=net,
                    tax_amount=tax,
                    gross_amount=net + tax,
                )
            )
        zero = round_half_up(Decimal(0), decimals)
        return TaxResult(
            engine=ENGINE_ID,
            rules_version=RULES_VERSION,
            jurisdiction=jurisdiction.code,
            jurisdiction_name=jurisdiction.name,
            tax_name=jurisdiction.tax_name,
            currency=jurisdiction.currency,
            prices_include_tax=request.prices_include_tax,
            lines=tuple(lines),
            net_total=sum((line.net_amount for line in lines), zero),
            tax_total=sum((line.tax_amount for line in lines), zero),
            gross_total=sum((line.gross_amount for line in lines), zero),
        )


def _jurisdiction_for(request: TaxRequest) -> tuple[Jurisdiction, bool]:
    """Pick the rules: domestic sales use the destination, exports the seller's country."""
    origin, destination = request.ship_from, request.ship_to
    if origin.country != destination.country:
        if origin.country in _GST_VAT_COUNTRIES:
            return _BY_CODE[origin.country], True
        raise UnsupportedError(
            f"Sales from {origin.country} to {destination.country} are not supported "
            "by the simple engine."
        )
    if destination.country == "US":
        code = f"US-{destination.region}" if destination.region else None
        if code is None or code not in _BY_CODE:
            state = destination.region or "unknown state"
            raise UnsupportedError(
                f"US state {state} is not supported by the simple engine "
                "(only states without local sales tax: MI, IN)."
            )
        return _BY_CODE[code], False
    if destination.country in _BY_CODE:
        return _BY_CODE[destination.country], False
    raise UnsupportedError(f"Country {destination.country} is not supported by the simple engine.")


def _tax_on(amount: Decimal, rate: Decimal, inclusive: bool) -> Decimal:
    if inclusive:
        return amount * rate / (1 + rate)
    return amount * rate


def _round_down_per_rate(
    unrounded: list[Decimal], rules: list[Rule], decimals: int
) -> list[Decimal]:
    """Round once per rate group (down), then share the group tax across its lines.

    Each line gets its rounded-down share; leftover units go to the lines with the largest
    remainders, so line taxes always add up to the group total.
    """
    unit = Decimal(1).scaleb(-decimals)
    groups: dict[Decimal, list[int]] = defaultdict(list)
    for index, rule in enumerate(rules):
        groups[rule.rate].append(index)

    taxes = [Decimal(0)] * len(unrounded)
    for indexes in groups.values():
        group_total = round_down(sum((unrounded[i] for i in indexes), Decimal(0)), decimals)
        shares = {i: round_down(unrounded[i], decimals) for i in indexes}
        leftover = int((group_total - sum(shares.values(), Decimal(0))) / unit)
        by_remainder = sorted(indexes, key=lambda i: unrounded[i] - shares[i], reverse=True)
        for i in by_remainder[:leftover]:
            shares[i] += unit
        for i, share in shares.items():
            taxes[i] = share
    return taxes
