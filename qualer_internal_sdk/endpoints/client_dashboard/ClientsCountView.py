"""Fetch client counts by filter type from Qualer ClientDashboard API."""

from utils.auth import QualerAPIFetcher
from .types import FilterType
from .response_types import ClientsCountViewResponse


def clients_count_view(
    search: str = "",
    filter_type: FilterType = FilterType.AllClients,
) -> ClientsCountViewResponse:
    """
    Fetch client counts grouped by filter type.

    Args:
        search: Search string to filter clients (default: "")
        filter_type: Type of filter to apply (default: FilterType.AllClients)

    Returns:
        ClientsCountViewResponse: Typed response with Success flag and view containing
            client counts grouped by filter type (AllClients, Prospect, Delinquent,
            Inactive, Unapproved, Hidden, OfflineFulfillment, AssetsDue,
            AssetsPastDue, AssetsPastDuePeriod)

    Example:
        >>> from qualer_internal_sdk.endpoints.client_dashboard import clients_count_view, FilterType
        >>> counts = clients_count_view(filter_type=FilterType.Inactive)
        >>> print(f"Inactive clients: {counts['view']['Inactive']}")
    """
    with QualerAPIFetcher() as api:
        return api.execute_endpoint(
            method="GET",
            endpoint_path="/ClientDashboard/ClientsCountView",
            auth_context_page="/ClientDashboard/Clients",
            params={"Search": search, "FilterType": filter_type.value},
        )
