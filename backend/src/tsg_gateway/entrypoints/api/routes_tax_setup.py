"""Tax setup API: categories, products, product groups, default category."""

from typing import Annotated

from fastapi import APIRouter, Body, Query, Response
from pydantic import BaseModel, ConfigDict
from starlette import status

from tsg_gateway.application.tax_setup import ProductStatus, ProductView, SetupSummary
from tsg_gateway.domain.products import GroupMapping, Product, ResolvedCategory, TaxSettings
from tsg_gateway.domain.tax_categories import TaxCategory
from tsg_gateway.entrypoints.api.dependencies import ServicesDep, SetupWriterDep, TenantDep

router = APIRouter(prefix="/v1", tags=["tax setup"])


class ProductInput(BaseModel):
    """Body for creating or replacing a product (the SKU is in the path)."""

    model_config = ConfigDict(extra="forbid")

    name: str
    group: str | None = None
    tax_category: str | None = None
    description: str | None = None


class GroupInput(BaseModel):
    """Body for a group mapping (the group is in the path)."""

    model_config = ConfigDict(extra="forbid")

    tax_category: str


class ImportResult(BaseModel):
    """Result of a bulk import."""

    imported: int


class ResolveInput(BaseModel):
    """Which category would a line with these details use?"""

    model_config = ConfigDict(extra="forbid")

    sku: str | None = None
    product_group: str | None = None
    tax_category: str | None = None


class SettingsInput(BaseModel):
    """Body for tax settings."""

    model_config = ConfigDict(extra="forbid")

    default_category: str


@router.get("/tax-categories")
async def list_tax_categories(services: ServicesDep) -> list[TaxCategory]:
    return services.tax_setup.list_categories()


@router.post("/tax-categories/resolve")
async def resolve_tax_category(
    body: ResolveInput, tenant: TenantDep, services: ServicesDep
) -> ResolvedCategory:
    return await services.tax_setup.resolve(
        tenant, sku=body.sku, group=body.product_group, line_category=body.tax_category
    )


@router.get("/tax-setup/summary")
async def tax_setup_summary(tenant: TenantDep, services: ServicesDep) -> SetupSummary:
    return await services.tax_setup.summary(tenant)


@router.get("/tax-settings")
async def get_tax_settings(tenant: TenantDep, services: ServicesDep) -> TaxSettings:
    return await services.tax_setup.get_settings(tenant)


@router.put("/tax-settings")
async def update_tax_settings(
    body: SettingsInput, tenant: SetupWriterDep, services: ServicesDep
) -> TaxSettings:
    return await services.tax_setup.update_settings(tenant, body.default_category)


@router.get("/products")
async def list_products(
    tenant: TenantDep,
    services: ServicesDep,
    search: str | None = None,
    tax_category: str | None = None,
    product_status: Annotated[ProductStatus, Query(alias="status")] = ProductStatus.ALL,
) -> list[ProductView]:
    return await services.tax_setup.list_products(
        tenant, search=search, tax_category=tax_category, status=product_status
    )


@router.post("/products/import")
async def import_products(
    body: Annotated[list[Product], Body(max_length=5000)],
    tenant: SetupWriterDep,
    services: ServicesDep,
) -> ImportResult:
    return ImportResult(imported=await services.tax_setup.upsert_products(tenant, body))


@router.get("/products/{sku}")
async def get_product(sku: str, tenant: TenantDep, services: ServicesDep) -> ProductView:
    return await services.tax_setup.get_product(tenant, sku)


@router.put("/products/{sku}")
async def put_product(
    sku: str, body: ProductInput, tenant: SetupWriterDep, services: ServicesDep
) -> ProductView:
    return await services.tax_setup.upsert_product(tenant, Product(sku=sku, **body.model_dump()))


@router.delete("/products/{sku}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(sku: str, tenant: SetupWriterDep, services: ServicesDep) -> Response:
    await services.tax_setup.delete_product(tenant, sku)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/product-groups")
async def list_product_groups(tenant: TenantDep, services: ServicesDep) -> list[GroupMapping]:
    return await services.tax_setup.list_groups(tenant)


@router.put("/product-groups/{group}")
async def put_product_group(
    group: str, body: GroupInput, tenant: SetupWriterDep, services: ServicesDep
) -> GroupMapping:
    return await services.tax_setup.upsert_group(tenant, group, body.tax_category)


@router.delete("/product-groups/{group}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_group(
    group: str, tenant: SetupWriterDep, services: ServicesDep
) -> Response:
    await services.tax_setup.delete_group(tenant, group)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
