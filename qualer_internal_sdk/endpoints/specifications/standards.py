"""
Specifications endpoint module.

Provides access to the Standard_Read endpoint which returns standards
(metadata about specifications/procedures) in Kendo DataSource format.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import os
import requests

from utils.auth import QualerAPIFetcher


@dataclass
class Standard:
    """Represents a standard/specification record returned by Standard_Read."""

    # Required fields
    id: int
    standard_title: str
    standard_subtitle: str
    asset_related: bool
    standard_group_id: int
    company_id: int
    group_name: str
    group_source: str
    manufacturer_part_number: str
    product_name: str
    manufacturer_name: str
    category_name: str
    product_id: int
    category_id: int
    manufacturer_id: int
    specification_count: int
    asset_has_image: bool
    has_image: bool
    parent_has_image: bool
    is_generic: bool
    asset_count: int
    updated_on: str
    updated_by_id: int
    updated_by: str
    apply_force: bool
    apply_fit: bool

    # Optional fields (nullable in API response)
    display_part_number: Optional[str]
    display_name: Optional[str]
    parent_product_name: Optional[str]
    root_category_name: Optional[str]
    parent_product_id: Optional[int]
    root_category_id: Optional[int]
    asset_id: Optional[int]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Standard":
        """Create a Standard instance from API response data."""
        return cls(
            id=data["Id"],
            standard_title=data["StandardTitle"],
            standard_subtitle=data["StandardSubtitle"],
            asset_related=data["AssetRelated"],
            standard_group_id=data["StandardGroupId"],
            company_id=data["CompanyId"],
            group_name=data["GroupName"],
            group_source=data["GroupSource"],
            manufacturer_part_number=data["ManufacturerPartNumber"],
            product_name=data["ProductName"],
            manufacturer_name=data["ManufacturerName"],
            category_name=data["CategoryName"],
            product_id=data["ProductId"],
            category_id=data["CategoryId"],
            manufacturer_id=data["ManufacturerId"],
            specification_count=data["SpecificationCount"],
            asset_has_image=data["AssetHasImage"],
            has_image=data["HasImage"],
            parent_has_image=data["ParentHasImage"],
            is_generic=data["IsGeneric"],
            asset_count=data["AssetCount"],
            updated_on=data["UpdatedOn"],
            updated_by_id=data["UpdatedById"],
            updated_by=data["UpdatedBy"],
            apply_force=data["ApplyForce"],
            apply_fit=data["ApplyFit"],
            display_part_number=data.get("DisplayPartNumber"),
            display_name=data.get("DisplayName"),
            parent_product_name=data.get("ParentProductName"),
            root_category_name=data.get("RootCategoryName"),
            parent_product_id=data.get("ParentProductId"),
            root_category_id=data.get("RootCategoryId"),
            asset_id=data.get("AssetId"),
        )


@dataclass
class StandardsPage:
    """Container for a single page of standards plus total count."""

    items: List[Standard]
    total: int


def _build_form_data(
    page: int,
    page_size: int,
    sort: str,
    group: str,
    filter_param: str,
    standard_filter: str,
    search: str,
    product_id: str,
    area_id: str,
) -> Dict[str, Any]:
    return {
        "sort": sort,
        "page": page,
        "pageSize": page_size,
        "group": group,
        "filter": filter_param,
        "StandardFilter": standard_filter,
        "Search": search,
        "ProductId": product_id,
        "AreaId": area_id,
    }


def get_standards_page(
    fetcher: QualerAPIFetcher,
    page: int = 1,
    page_size: int = 50,
    sort: str = "",
    group: str = "",
    filter_param: str = "",
    standard_filter: str = "All",
    search: str = "",
    product_id: str = "",
    area_id: Optional[str] = None,
) -> StandardsPage:
    """
    Fetch a single page of standards from the Standard_Read endpoint.

    Args:
        fetcher: Authenticated QualerAPIFetcher instance
        page: Page number (1-based)
        page_size: Number of records per page
        sort: Kendo sort expression
        group: Kendo group expression
        filter_param: Kendo filter expression
        standard_filter: StandardFilter parameter (e.g., "All")
        search: Search term
        product_id: ProductId filter
        area_id: AreaId filter (use None to send "NaN" as seen in Qualer UI)

    Returns:
        StandardsPage containing the items and the reported total count

    Raises:
        requests.exceptions.HTTPError: If the API reports errors
    """
    url = "https://jgiquality.qualer.com/specifications/Standard_Read"
    referer = "https://jgiquality.qualer.com/specifications"

    area_id_value = "NaN" if area_id is None else str(area_id)
    form_data = _build_form_data(
        page=page,
        page_size=page_size,
        sort=sort,
        group=group,
        filter_param=filter_param,
        standard_filter=standard_filter,
        search=search,
        product_id=product_id,
        area_id=area_id_value,
    )

    timeout = float(os.getenv("QUALER_REQUEST_TIMEOUT", "30"))
    response = fetcher.post(
        url,
        data=form_data,
        referer=referer,
        timeout=timeout,
    )

    response_dict = response.json()
    errors = response_dict.get("Errors")
    if errors:
        raise requests.exceptions.HTTPError(
            f"API returned errors: {errors}",
            response=response,
        )

    data = response_dict.get("Data", [])
    total = int(response_dict.get("Total", len(data)))
    return StandardsPage(items=[Standard.from_dict(item) for item in data], total=total)


def get_all_standards(
    fetcher: QualerAPIFetcher,
    page_size: int = 100,
    sort: str = "",
    group: str = "",
    filter_param: str = "",
    standard_filter: str = "All",
    search: str = "",
    product_id: str = "",
    area_id: Optional[str] = None,
    max_pages: Optional[int] = None,
) -> List[Standard]:
    """
    Fetch all standards by paging through Standard_Read.

    Warning: Total can be large (e.g., 10k+ records). Use `max_pages` to
    limit for sampling/testing.
    """
    results: List[Standard] = []
    page = 1

    while True:
        page_data = get_standards_page(
            fetcher=fetcher,
            page=page,
            page_size=page_size,
            sort=sort,
            group=group,
            filter_param=filter_param,
            standard_filter=standard_filter,
            search=search,
            product_id=product_id,
            area_id=area_id,
        )

        results.extend(page_data.items)

        # Stop if we've reached the reported total
        if len(results) >= page_data.total:
            break

        page += 1
        if max_pages is not None and page > max_pages:
            break

    return results
