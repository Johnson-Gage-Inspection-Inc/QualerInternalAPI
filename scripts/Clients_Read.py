"""
Fetch client list from Qualer and save to data/clients.json.

This script authenticates to Qualer, fetches the complete list of clients,
and saves the response as JSON for use by other extraction scripts.
"""

import json
from utils.auth import QualerAPIFetcher


def clients_read(page_size: int = 1000000) -> dict:
    """
    Fetch all clients from Qualer ClientDashboard API.

    Args:
        page_size: Number of results to fetch per page (default: 1000000)

    Returns:
        Dictionary containing the API response with client data
    """
    with QualerAPIFetcher(headless=False) as api:
        # Navigate to clients page first to establish proper browser context and cookies
        print("Navigating to clients page...")
        if not api.driver:
            raise RuntimeError("Failed to initialize Selenium driver")
        api.driver.get("https://jgiquality.qualer.com/clients")

        # Give page time to load and render
        from time import sleep

        sleep(3)

        # Extract CSRF token from page source
        print("Extracting CSRF token...")
        page_source = api.driver.page_source
        csrf_token = api.extract_csrf_token(page_source)
        print(f"✓ Got CSRF token: {csrf_token[:20]}...")

        url = "https://jgiquality.qualer.com/ClientDashboard/Clients_Read"

        # Request parameters matching the web UI - MUST include CSRF token
        payload = {
            "sort": "ClientCompanyName-asc",
            "page": 1,
            "pageSize": page_size,
            "group": "",
            "filter": "",
            "search": "",
            "filterType": "AllClients",
            "__RequestVerificationToken": csrf_token,  # CRITICAL: Include CSRF token
        }

        # Headers for the API request
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache, must-revalidate",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://jgiquality.qualer.com",
            "pragma": "no-cache",
            "referer": "https://jgiquality.qualer.com/clients",
            "x-requested-with": "XMLHttpRequest",
        }

        try:
            if not api.session:
                raise RuntimeError("Failed to establish authenticated session")
            print("Fetching client list...")
            response = api.session.post(url, data=payload, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching clients: {e}")
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            if "response" in locals():
                print(f"Response text: {response.text[:500]}")
            raise


def main():
    """Fetch clients and save to data/clients.json."""
    print("Fetching clients from Qualer...")

    clients_data = clients_read()

    # Save to file
    with open("data/clients.json", "w", encoding="utf-8") as f:
        json.dump(clients_data, f, indent=2)

    # Print summary
    if isinstance(clients_data, dict):
        total = clients_data.get("total", len(clients_data.get("data", [])))
        print(f"✓ Saved {total} clients to data/clients.json")
    else:
        print(f"✓ Saved {len(clients_data)} clients to data/clients.json")


if __name__ == "__main__":
    main()
