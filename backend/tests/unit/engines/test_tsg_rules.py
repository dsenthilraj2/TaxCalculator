from decimal import Decimal

import pytest

from tsg_gateway.adapters.engines.tsg_rules.engine import TsgRulesEngine
from tsg_gateway.domain.canonical.tax import (
    Address,
    Customer,
    CustomerExemption,
    TaxLine,
    TaxRequest,
    Treatment,
)
from tsg_gateway.domain.errors import UnsupportedError


def _request(
    country: str,
    currency: str,
    *lines: tuple[str, str],
    to_country: str | None = None,
    region: str | None = None,
    inclusive: bool = False,
    exemption: CustomerExemption = CustomerExemption.NONE,
) -> TaxRequest:
    return TaxRequest(
        currency=currency,
        prices_include_tax=inclusive,
        ship_from=Address(country=country, region=region),
        ship_to=Address(country=to_country or country, region=region),
        customer=Customer(exemption=exemption),
        lines=tuple(
            TaxLine(
                line_id=str(i),
                tax_category=category,
                quantity=Decimal(1),
                unit_price=Decimal(price),
            )
            for i, (category, price) in enumerate(lines, start=1)
        ),
    )


async def test_japan_rounds_once_per_rate_and_lines_add_up() -> None:
    # Food 8%: 0.4 + 0.4 + 0.4 = 1.2 -> group tax 1 yen, given to one line.
    request = _request("JP", "JPY", ("TSG-FOOD", "5"), ("TSG-FOOD", "5"), ("TSG-FOOD", "5"))

    result = await TsgRulesEngine().calculate(request)

    assert result.tax_total == Decimal(1)
    assert sorted(line.tax_amount for line in result.lines) == [0, 0, 1]


async def test_japan_inclusive_prices() -> None:
    result = await TsgRulesEngine().calculate(
        _request("JP", "JPY", ("TSG-GEN", "1100"), inclusive=True)
    )

    assert result.tax_total == Decimal(100)
    assert result.net_total == Decimal(1000)


async def test_export_is_labelled_export() -> None:
    result = await TsgRulesEngine().calculate(
        _request("AU", "AUD", ("TSG-GEN", "200.00"), to_country="NZ")
    )

    assert result.lines[0].treatment is Treatment.EXPORT
    assert result.jurisdiction == "AU"


async def test_resale_certificate_ignored_for_gst() -> None:
    result = await TsgRulesEngine().calculate(
        _request("AU", "AUD", ("TSG-GEN", "100.00"), exemption=CustomerExemption.RESALE)
    )

    assert result.tax_total == Decimal("10.00")


async def test_exempt_and_zero_rated_are_labelled_differently() -> None:
    result = await TsgRulesEngine().calculate(
        _request("GB", "GBP", ("TSG-FIN", "100.00"), ("TSG-CLOTH-CHILD", "100.00"))
    )

    assert [line.treatment for line in result.lines] == [Treatment.EXEMPT, Treatment.ZERO_RATED]


async def test_unverified_us_category_is_unsupported() -> None:
    with pytest.raises(UnsupportedError, match="TSG-ENERGY-HOME"):
        await TsgRulesEngine().calculate(
            _request("US", "USD", ("TSG-ENERGY-HOME", "100.00"), region="MI")
        )


def test_lists_seven_jurisdictions() -> None:
    codes = [j.code for j in TsgRulesEngine().jurisdictions()]
    assert codes == ["AU", "NZ", "SG", "JP", "GB", "US-MI", "US-IN"]
