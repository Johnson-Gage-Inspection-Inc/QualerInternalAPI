"""Fetch all clients from Qualer ClientDashboard API."""

import logging
import os
from time import sleep
from typing import cast

import requests

from utils.auth import QualerAPIFetcher
from .types import FilterType, SortField, SortOrder
from .response_types import ClientsReadResponse

logger = logging.getLogger(__name__)


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
        # Navigate to clients page first to establish authenticated browser context
        logger.info("Navigating to clients page...")
        if not api.driver:
            raise RuntimeError("Failed to initialize Selenium driver")
        api.driver.get("https://jgiquality.qualer.com/clients")

        # Get configurable page load wait time (default 3 seconds)
        page_load_wait = float(os.getenv("QUALER_PAGE_LOAD_WAIT_TIME", "3"))
        logger.debug(f"Waiting {page_load_wait}s for page to load and render")
        sleep(page_load_wait)

        # QualerAPIFetcher automatically syncs cookies from the browser to the session,
        # including the CSRF cookie, which may use a suffixed name
        # (e.g., __RequestVerificationToken_L3...).

        # Extract CSRF token from the hidden form field, which uses the standard
        # field name "__RequestVerificationToken" even when the corresponding
        # cookie name is suffixed. ASP.NET uses a double-submit cookie pattern:
        # cookie token + form token.
        try:
            csrf_token = api.extract_csrf_token(api.driver.page_source)
        except ValueError as e:
            # If CSRF token is not present, skip HTTP path and fall back to browser-based fetch
            logger.warning(
                f"Failed to extract CSRF token from clients page: {e}. "
                "Falling back to browser fetch."
            )
            payload = {
                "sort": f"{sort_by.value}-{sort_order.value}",
                "page": page,
                "pageSize": page_size,
                "group": group,
                "filter": filter_str,
                "search": search,
                "filterType": filter_type.value,
            }
            logger.info("Fetching client data via browser context (no CSRF token available)...")
            return cast(
                ClientsReadResponse,
                api.fetch_via_browser(
                    method="POST",
                    endpoint_path="/ClientDashboard/Clients_Read",
                    auth_context_page="/clients",
                    params=payload,
                ),
            )

        # Try HTTP POST first (fast path)
        payload = {
            "sort": f"{sort_by.value}-{sort_order.value}",
            "page": page,
            "pageSize": page_size,
            "group": group,
            "filter": filter_str,
            "search": search,
            "filterType": filter_type.value,
            "__RequestVerificationToken": csrf_token,  # Always use standard field name
        }

        headers = api.get_headers(
            referer="https://jgiquality.qualer.com/clients",
            x_requested_with="XMLHttpRequest",
            content_type="application/x-www-form-urlencoded; charset=UTF-8",
        )

        logger.info("Attempting HTTP POST (session)...")
        try:
            if not api.session:
                raise RuntimeError("Failed to establish authenticated session")
            response = api.session.post(
                "https://jgiquality.qualer.com/ClientDashboard/Clients_Read",
                data=payload,
                headers=headers,
                timeout=30,
            )
            logger.info(f"HTTP POST status: {response.status_code}")
            if response.status_code == 200:
                logger.info("HTTP POST succeeded!")
                return cast(ClientsReadResponse, response.json())
            else:
                logger.info(
                    f"HTTP POST returned {response.status_code}, " "falling back to browser fetch"
                )
        except (requests.RequestException, ValueError, RuntimeError) as e:
            logger.warning(f"HTTP POST failed: {e}, falling back to browser fetch")

        # Fallback to browser-based fetch (known-good path)
        logger.info("Fetching client data via browser context...")
        return cast(
            ClientsReadResponse,
            api.fetch_via_browser(
                method="POST",
                endpoint_path="/ClientDashboard/Clients_Read",
                auth_context_page="/clients",
                params=payload,
            ),
        )
