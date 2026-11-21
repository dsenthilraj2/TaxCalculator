"""TSG tax categories: the provider-neutral product taxonomy (spec/tax-reference/README.md).

Clients map their products to these codes once. Provider-specific codes are a translation
of these, so switching provider never means remapping a catalogue.
"""

from pydantic import BaseModel, ConfigDict

from tsg_gateway.domain.errors import InvalidRequestError

DEFAULT_TAX_CATEGORY = "TSG-GEN"


class TaxCategory(BaseModel):
    """One TSG tax category."""

    model_config = ConfigDict(frozen=True)

    code: str
    name: str
    description: str


TAX_CATEGORIES: tuple[TaxCategory, ...] = (
    TaxCategory(
        code="TSG-GEN",
        name="General goods",
        description="Everyday taxable goods: electronics, furniture, tools",
    ),
    TaxCategory(
        code="TSG-FOOD",
        name="Basic food",
        description="Groceries for home: bread, milk, fruit, vegetables",
    ),
    TaxCategory(
        code="TSG-FOOD-PREP",
        name="Prepared food / dining",
        description="Hot food, restaurant meals, catering",
    ),
    TaxCategory(code="TSG-ALC", name="Alcohol", description="Beer, wine, spirits"),
    TaxCategory(
        code="TSG-MED-RX",
        name="Prescription medicine",
        description="Medicines dispensed on prescription",
    ),
    TaxCategory(
        code="TSG-EDU",
        name="Education course",
        description="Tuition from a recognised education provider",
    ),
    TaxCategory(
        code="TSG-FIN",
        name="Financial service",
        description="Loan interest, bank fees, insurance",
    ),
    TaxCategory(
        code="TSG-CLOTH-CHILD",
        name="Children's clothing",
        description="Clothes and shoes for young children",
    ),
    TaxCategory(
        code="TSG-ENERGY-HOME",
        name="Home energy",
        description="Electricity and gas for a household",
    ),
    TaxCategory(
        code="TSG-NEWS",
        name="Newspaper subscription",
        description="Printed newspaper delivered regularly",
    ),
    TaxCategory(code="TSG-BOOK", name="Books", description="Printed books"),
)

_BY_CODE = {category.code: category for category in TAX_CATEGORIES}


def get_tax_category(code: str) -> TaxCategory | None:
    """Return the category for ``code``, or ``None`` if it is not a TSG category."""
    return _BY_CODE.get(code)


def require_tax_category(code: str) -> str:
    """Return ``code`` if it is a known TSG category, otherwise raise ``InvalidRequestError``."""
    if code not in _BY_CODE:
        raise InvalidRequestError(f"Unknown tax category '{code}'.")
    return code
