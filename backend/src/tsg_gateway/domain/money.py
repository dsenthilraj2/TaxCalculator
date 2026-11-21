"""Money helpers. Amounts are always ``Decimal``; rounding is always explicit."""

from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

_ZERO_DECIMAL_CURRENCIES = frozenset({"JPY"})


def currency_decimals(currency: str) -> int:
    """Number of minor-unit decimals for an ISO 4217 currency (JPY has none)."""
    return 0 if currency in _ZERO_DECIMAL_CURRENCIES else 2


def quantum(decimals: int) -> Decimal:
    """The smallest unit for ``decimals`` places, e.g. ``Decimal('0.01')``."""
    return Decimal(1).scaleb(-decimals)


def round_half_up(value: Decimal, decimals: int) -> Decimal:
    """Round to ``decimals`` places, halves away from zero."""
    return value.quantize(quantum(decimals), rounding=ROUND_HALF_UP)


def round_down(value: Decimal, decimals: int) -> Decimal:
    """Round towards zero to ``decimals`` places."""
    return value.quantize(quantum(decimals), rounding=ROUND_DOWN)
