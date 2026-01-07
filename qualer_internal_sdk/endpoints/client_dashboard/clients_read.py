"""Fetch all clients from Qualer ClientDashboard API."""

from time import sleep

from utils.auth import QualerAPIFetcher


def clients_read(
    sort: str = "ClientCompanyName-asc",
    page: int = 1,
    page_size: int = 1000000,
    group: str = "",
    filter: str = "",
    search: str = "",
    filter_type: str = "AllClients",
) -> dict:
    """
    Fetch all clients from Qualer ClientDashboard API.

    Endpoint: POST /ClientDashboard/Clients_Read

    Args:
        page_size: Number of results to fetch per page (default: 1000000)

    Returns:
        Dictionary containing the API response with client data
    """
    with QualerAPIFetcher() as api:
        # Navigate to clients page first to establish proper browser context and cookies
        print("Navigating to clients page...")
        if not api.driver:
            raise RuntimeError("Failed to initialize Selenium driver")
        clients_page_url = "https://jgiquality.qualer.com/clients"
        api.driver.get(clients_page_url)

        # Give page time to load and render
        sleep(3)

        # Extract CSRF token from page source
        print("Extracting CSRF token...")
        page_source = api.driver.page_source
        csrf_token = api.extract_csrf_token(page_source)
        print(f"✓ Got CSRF token: {csrf_token[:20]}...")

        url = "https://jgiquality.qualer.com/ClientDashboard/Clients_Read"

        # Request parameters matching the web UI - MUST include CSRF token
        payload = {
            "sort": sort,
            "page": page,
            "pageSize": page_size,
            "group": group,
            "filter": filter,
            "search": search,
            "filterType": filter_type,
            "__RequestVerificationToken": csrf_token,  # CRITICAL: Include CSRF token
        }

        try:
            print("Fetching client list...")
            # Use api.post() for simplified header management - handles all standard headers
            response = api.post(url, data=payload, referer=clients_page_url, timeout=30)
            return response.json()
        except Exception as e:
            print(f"Error fetching clients: {e}")
            raise
