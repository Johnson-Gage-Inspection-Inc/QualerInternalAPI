"""Fetch all clients from Qualer ClientDashboard API."""

from time import sleep
from urllib.parse import urlencode

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

    Raises:
        RuntimeError: If Selenium driver initialization fails

    Note:
        This endpoint requires JavaScript execution in browser context.
        Direct HTTP POST requests fail with 401 even with valid cookies/CSRF tokens.
    """
    with QualerAPIFetcher() as api:
        # Navigate to clients page to establish authenticated browser context
        print("Navigating to clients page...")
        if not api.driver:
            raise RuntimeError("Failed to initialize Selenium driver")
        clients_page_url = "https://jgiquality.qualer.com/clients"
        api.driver.get(clients_page_url)

        # Give page time to load and render
        sleep(3)

        # Extract CSRF token from page
        print("Extracting CSRF token...")
        csrf_token = api.extract_csrf_token(api.driver.page_source)

        url = "https://jgiquality.qualer.com/ClientDashboard/Clients_Read"

        # Build POST payload
        payload = {
            "sort": f"{sort_by.value}-{sort_order.value}",
            "page": page,
            "pageSize": page_size,
            "group": group,
            "filter": filter_str,
            "search": search,
            "filterType": filter_type.value,
            "__RequestVerificationToken": csrf_token,
        }

        # URL-encode payload for JavaScript fetch
        payload_str = urlencode(payload)

        print("Fetching client list...")
        # Use JavaScript fetch to maintain browser authentication context
        result = api.driver.execute_async_script(
            f"""
            var callback = arguments[arguments.length - 1];
            fetch("{url}", {{
                method: "POST",
                headers: {{
                    "accept": "*/*",
                    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "x-requested-with": "XMLHttpRequest"
                }},
                body: "{payload_str}",
                credentials: "include"
            }})
            .then(response => response.json())
            .then(callback)
            .catch(err => callback({{error: err.toString()}}));
        """
        )

        if result.get("error"):
            raise RuntimeError(f"JavaScript fetch failed: {result['error']}")

        return result
