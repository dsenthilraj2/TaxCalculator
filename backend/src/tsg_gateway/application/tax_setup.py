"""Product → tax category setup: the first thing a new client configures."""

from collections.abc import Sequence
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from tsg_gateway.domain.errors import InvalidRequestError, NotFoundError
from tsg_gateway.domain.products import (
    CategorySource,
    GroupMapping,
    Product,
    ResolvedCategory,
    TaxSettings,
    resolve_tax_category,
)
from tsg_gateway.domain.tax_categories import TAX_CATEGORIES, TaxCategory, require_tax_category
from tsg_gateway.ports.tax_setup import (
    GroupMappingRepository,
    ProductRepository,
    TaxSettingsRepository,
)


class ProductStatus(StrEnum):
    """Filter for the product list."""

    ALL = "all"
    MAPPED = "mapped"
    UNMAPPED = "unmapped"


class ProductView(Product):
    """A product with the category it would actually be taxed under."""

    resolved_category: str
    category_source: CategorySource


class SetupSummary(BaseModel):
    """Counts for the dashboard."""

    model_config = ConfigDict(frozen=True)

    products_total: int
    products_by_product: int
    products_by_group: int
    products_by_default: int
    groups_total: int
    default_category: str


class TaxSetupService:
    """Use cases for products, group mappings and the client default category."""

    def __init__(
        self,
        products: ProductRepository,
        groups: GroupMappingRepository,
        settings: TaxSettingsRepository,
    ) -> None:
        self._products = products
        self._groups = groups
        self._settings = settings

    # ---------------------------------------------------------------- categories
    @staticmethod
    def list_categories() -> list[TaxCategory]:
        """All TSG tax categories."""
        return list(TAX_CATEGORIES)

    # ---------------------------------------------------------------- settings
    async def get_settings(self, tenant_id: str) -> TaxSettings:
        """Client settings, or defaults if never saved."""
        return await self._settings.get(tenant_id) or TaxSettings()

    async def update_settings(self, tenant_id: str, default_category: str) -> TaxSettings:
        """Change the category used when nothing else matches."""
        settings = TaxSettings(default_category=require_tax_category(default_category))
        await self._settings.save(tenant_id, settings)
        return settings

    # ---------------------------------------------------------------- groups
    async def list_groups(self, tenant_id: str) -> list[GroupMapping]:
        """Group mappings, sorted by group name."""
        return sorted(await self._groups.list_all(tenant_id), key=lambda m: m.group.lower())

    async def upsert_group(self, tenant_id: str, group: str, tax_category: str) -> GroupMapping:
        """Create or change a group mapping."""
        mapping = GroupMapping(
            group=_required(group, "Group"), tax_category=require_tax_category(tax_category)
        )
        await self._groups.upsert(tenant_id, mapping)
        return mapping

    async def delete_group(self, tenant_id: str, group: str) -> None:
        """Remove a group mapping."""
        if not await self._groups.delete(tenant_id, group):
            raise NotFoundError(f"Product group '{group}' has no mapping.")

    # ---------------------------------------------------------------- products
    async def list_products(
        self,
        tenant_id: str,
        *,
        search: str | None = None,
        tax_category: str | None = None,
        status: ProductStatus = ProductStatus.ALL,
    ) -> list[ProductView]:
        """Products with their effective category, filtered and sorted by SKU."""
        products = await self._products.list_all(tenant_id)
        views = await self._views(tenant_id, products)
        needle = search.strip().lower() if search else ""
        result = []
        for view in views:
            if needle and not _matches(view, needle):
                continue
            if tax_category and view.resolved_category != tax_category:
                continue
            is_default = view.category_source is CategorySource.DEFAULT
            if status is ProductStatus.MAPPED and is_default:
                continue
            if status is ProductStatus.UNMAPPED and not is_default:
                continue
            result.append(view)
        return sorted(result, key=lambda v: v.sku.lower())

    async def get_product(self, tenant_id: str, sku: str) -> ProductView:
        """One product with its effective category."""
        product = await self._products.get(tenant_id, sku)
        if product is None:
            raise NotFoundError(f"Product '{sku}' not found.")
        return (await self._views(tenant_id, [product]))[0]

    async def upsert_product(self, tenant_id: str, product: Product) -> ProductView:
        """Create or replace a product."""
        clean = _validated(product)
        await self._products.upsert(tenant_id, clean)
        return (await self._views(tenant_id, [clean]))[0]

    async def upsert_products(self, tenant_id: str, products: Sequence[Product]) -> int:
        """Create or replace many products (import). All are validated before any is saved."""
        clean = [_validated(product) for product in products]
        skus = [product.sku for product in clean]
        if len(set(skus)) != len(skus):
            raise InvalidRequestError("Duplicate SKUs in import.")
        await self._products.upsert_many(tenant_id, clean)
        return len(clean)

    async def delete_product(self, tenant_id: str, sku: str) -> None:
        """Remove a product."""
        if not await self._products.delete(tenant_id, sku):
            raise NotFoundError(f"Product '{sku}' not found.")

    # ---------------------------------------------------------------- resolution
    async def resolve(
        self,
        tenant_id: str,
        *,
        sku: str | None = None,
        group: str | None = None,
        line_category: str | None = None,
    ) -> ResolvedCategory:
        """The category a sale line would use: line → product → group → default."""
        resolver = await self.resolver(tenant_id)
        return await resolver.resolve(sku=sku, group=group, line_category=line_category)

    async def resolver(self, tenant_id: str) -> "CategoryResolver":
        """A resolver that loads mappings once, for resolving many lines."""
        settings = await self.get_settings(tenant_id)
        mappings = {m.group: m.tax_category for m in await self._groups.list_all(tenant_id)}
        return CategoryResolver(tenant_id, self._products, mappings, settings.default_category)

    async def summary(self, tenant_id: str) -> SetupSummary:
        """Counts for the dashboard."""
        views = await self._views(tenant_id, await self._products.list_all(tenant_id))
        by_source = dict.fromkeys(CategorySource, 0)
        for view in views:
            by_source[view.category_source] += 1
        settings = await self.get_settings(tenant_id)
        return SetupSummary(
            products_total=len(views),
            products_by_product=by_source[CategorySource.PRODUCT],
            products_by_group=by_source[CategorySource.GROUP],
            products_by_default=by_source[CategorySource.DEFAULT],
            groups_total=len(await self._groups.list_all(tenant_id)),
            default_category=settings.default_category,
        )

    async def _views(self, tenant_id: str, products: Sequence[Product]) -> list[ProductView]:
        settings = await self.get_settings(tenant_id)
        mappings = {m.group: m.tax_category for m in await self._groups.list_all(tenant_id)}
        views = []
        for product in products:
            resolved = resolve_tax_category(
                line_category=None,
                product=product,
                group=None,
                group_mappings=mappings,
                default_category=settings.default_category,
            )
            views.append(
                ProductView(
                    **product.model_dump(),
                    resolved_category=resolved.tax_category,
                    category_source=resolved.source,
                )
            )
        return views


class CategoryResolver:
    """Resolves categories for many lines of one request with a single mapping load."""

    def __init__(
        self,
        tenant_id: str,
        products: ProductRepository,
        group_mappings: dict[str, str],
        default_category: str,
    ) -> None:
        self._tenant_id = tenant_id
        self._products = products
        self._group_mappings = group_mappings
        self._default_category = default_category

    async def resolve(
        self, *, sku: str | None, group: str | None, line_category: str | None
    ) -> ResolvedCategory:
        """Resolve one line. An explicit line category must be a known TSG category."""
        if line_category:
            require_tax_category(line_category)
        product = await self._products.get(self._tenant_id, sku) if sku else None
        return resolve_tax_category(
            line_category=line_category,
            product=product,
            group=group,
            group_mappings=self._group_mappings,
            default_category=self._default_category,
        )


def _required(value: str, label: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise InvalidRequestError(f"{label} is required.")
    return stripped


def _optional(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip() or None


def _validated(product: Product) -> Product:
    category = _optional(product.tax_category)
    return Product(
        sku=_required(product.sku, "SKU"),
        name=_required(product.name, "Name"),
        group=_optional(product.group),
        tax_category=require_tax_category(category) if category else None,
        description=_optional(product.description),
    )


def _matches(view: ProductView, needle: str) -> bool:
    fields = (view.sku, view.name, view.group or "", view.description or "")
    return any(needle in value.lower() for value in fields)
