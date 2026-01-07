"""Fetch all clients from Qualer ClientDashboard API."""

from typing import cast

from utils.auth import QualerAPIFetcher
from .types import FilterType, SortField, SortOrder
from .response_types import ClientsReadResponse


def clients_read(
    sort_by: SortField = SortField.ClientCompanyName,
    sort_order: SortOrder = SortOrder.Ascending,
    page: int = 1,
    page_size: int = 1000000,
    group: str = "",
    filter_str: str = "",
    search: str = "",
    filter_type: FilterType = FilterType.AllClients,
) -> ClientsReadResponse:
    """
    Fetch all clients from Qualer ClientDashboard API.

    Endpoint: POST /ClientDashboard/Clients_Read

    Args:
        sort_by: Field to sort by (default: SortField.ClientCompanyName)
            Options: ClientCompanyName, ClientAccountNumber, ContactName,
            CreatedDate, AssetCount, OrdersCount
        sort_order: Sort direction (default: SortOrder.Ascending)
            Options: Ascending, Descending
        page: Page number for pagination (default: 1)
        page_size: Number of results per page (default: 1000000)
        group: Group filter value (default: empty string)
        filter_str: Additional filter criteria (default: empty string)
        search: Search query string (default: empty string)
        filter_type: Type of filter to apply (default: FilterType.AllClients)
            Options: AllClients, Prospects, Delinquent, Inactive, Unapproved,
            Hidden, AssetsDue, AssetsPastDue

    Returns:
        ClientsReadResponse: Typed response with Data (list of client records),
            Total (total count), AggregateResults, and Errors fields

    Example:
        >>> from qualer_internal_sdk.endpoints.client_dashboard import clients_read
        >>> response = clients_read(page_size=10)
        >>> print(f"Fetched {len(response['Data'])} of {response['Total']} clients")
    """
    with QualerAPIFetcher() as api:
        return cast(
            ClientsReadResponse,
            api.fetch_via_browser(
                method="POST",
                endpoint_path="/ClientDashboard/Clients_Read",
                auth_context_page="/clients",
                params={
                    "sort": f"{sort_by.value}-{sort_order.value}",
                    "page": page,
                    "pageSize": page_size,
                    "group": group,
                    "filter": filter_str,
                    "search": search,
                    "filterType": filter_type.value,
                },
            ),
        )
