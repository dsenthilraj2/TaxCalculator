"""Client products and how each one maps to a TSG tax category."""

from collections.abc import Mapping
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from tsg_gateway.domain.tax_categories import DEFAULT_TAX_CATEGORY


class Product(BaseModel):
    """A product the client sells. ``tax_category`` set here overrides its group mapping."""

    model_config = ConfigDict(frozen=True)

    sku: str
    name: str
    group: str | None = None
    tax_category: str | None = None
    description: str | None = None


class GroupMapping(BaseModel):
    """Maps an ERP product group to a tax category. Every SKU in the group inherits it."""

    model_config = ConfigDict(frozen=True)

    group: str
    tax_category: str


class TaxSettings(BaseModel):
    """Per-client tax setup settings."""

    model_config = ConfigDict(frozen=True)

    default_category: str = DEFAULT_TAX_CATEGORY


class CategorySource(StrEnum):
    """Where a line's tax category came from, in lookup order."""

    LINE = "line"
    PRODUCT = "product"
    GROUP = "group"
    DEFAULT = "default"


class ResolvedCategory(BaseModel):
    """The tax category used for a line and why."""

    model_config = ConfigDict(frozen=True)

    tax_category: str
    source: CategorySource


def resolve_tax_category(
    *,
    line_category: str | None,
    product: Product | None,
    group: str | None,
    group_mappings: Mapping[str, str],
    default_category: str,
) -> ResolvedCategory:
    """Resolve a category: line → product → group → client default."""
    if line_category:
        return ResolvedCategory(tax_category=line_category, source=CategorySource.LINE)
    if product is not None and product.tax_category:
        return ResolvedCategory(tax_category=product.tax_category, source=CategorySource.PRODUCT)
    effective_group = group or (product.group if product is not None else None)
    if effective_group and effective_group in group_mappings:
        return ResolvedCategory(
            tax_category=group_mappings[effective_group], source=CategorySource.GROUP
        )
    return ResolvedCategory(tax_category=default_category, source=CategorySource.DEFAULT)
