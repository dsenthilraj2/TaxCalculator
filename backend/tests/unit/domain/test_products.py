from tsg_gateway.domain.products import CategorySource, Product, resolve_tax_category

GROUPS = {"Kids clothing": "TSG-CLOTH-CHILD"}


def _resolve(
    *,
    line_category: str | None = None,
    product: Product | None = None,
    group: str | None = None,
) -> tuple[str, CategorySource]:
    resolved = resolve_tax_category(
        line_category=line_category,
        product=product,
        group=group,
        group_mappings=GROUPS,
        default_category="TSG-GEN",
    )
    return resolved.tax_category, resolved.source


def test_line_category_wins() -> None:
    product = Product(sku="A", name="A", tax_category="TSG-BOOK")
    assert _resolve(line_category="TSG-FOOD", product=product) == ("TSG-FOOD", CategorySource.LINE)


def test_product_category_beats_group() -> None:
    product = Product(sku="A", name="A", group="Kids clothing", tax_category="TSG-BOOK")
    assert _resolve(product=product) == ("TSG-BOOK", CategorySource.PRODUCT)


def test_product_group_mapping_is_inherited() -> None:
    product = Product(sku="A", name="A", group="Kids clothing")
    assert _resolve(product=product) == ("TSG-CLOTH-CHILD", CategorySource.GROUP)


def test_line_group_used_for_unknown_product() -> None:
    assert _resolve(group="Kids clothing") == ("TSG-CLOTH-CHILD", CategorySource.GROUP)


def test_falls_back_to_default() -> None:
    product = Product(sku="A", name="A", group="Unmapped group")
    assert _resolve(product=product) == ("TSG-GEN", CategorySource.DEFAULT)
    assert _resolve() == ("TSG-GEN", CategorySource.DEFAULT)
