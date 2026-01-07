"""Service endpoint module for Qualer API.

Provides methods to fetch service group information from the Qualer system.
"""

from typing import Any, Dict, Optional
from requests import Session
from selenium.webdriver.remote.webdriver import WebDriver
from tqdm import tqdm


class ServiceGroupsEndpoint:
    """Encapsulates service groups API endpoint operations."""

    def __init__(self, session: Optional[Session], driver: Optional[WebDriver] = None):
        """Initialize the ServiceGroupsEndpoint.

        Args:
            session: Authenticated requests.Session object
            driver: Optional Selenium WebDriver for JavaScript-rendered content
        """
        self.session = session
        self.driver = driver

    def fetch_for_service_order_items(
        self, service_order_item_ids: list, service_name: str = "GetServiceGroupsForExistingLevels"
    ) -> Dict[int, Any]:
        """Fetch service groups for multiple service order items.

        Args:
            service_order_item_ids: List of service order item IDs to fetch groups for
            service_name: Service name for database storage

        Returns:
            Dictionary mapping service_order_item_id to API response

        Example:
            >>> endpoint = ServiceGroupsEndpoint(session)
            >>> results = endpoint.fetch_for_service_order_items([123, 456])
            >>> print(results[123])
        """
        results = {}
        for item_id in tqdm(service_order_item_ids, desc="Fetching service groups"):
            try:
                result = self.get_service_groups(item_id, service_name)
                results[item_id] = result
            except Exception as e:
                print(f"Warning: Failed to fetch service groups for item {item_id}: {e}")
                results[item_id] = {"error": str(e)}

        return results

    def get_service_groups(
        self, service_order_item_id: int, service_name: str = "GetServiceGroupsForExistingLevels"
    ) -> Dict[str, Any]:
        """Fetch service groups for a specific service order item.

        Args:
            service_order_item_id: Service order item ID
            service_name: Service name for database storage

        Returns:
            API response as dictionary

        Raises:
            RuntimeError: If session or driver is not available
            requests.HTTPError: On HTTP errors
        """
        if not self.session:
            raise RuntimeError("Session not available")

        url = (
            "https://jgiquality.qualer.com/work/TaskDetails/GetServiceGroupsForExistingLevels?"
            f"serviceOrderItemId={service_order_item_id}"
        )

        response = self.session.get(url, timeout=30)
        response.raise_for_status()

        # Store in database if driver is available
        if self.driver:
            self._store_response(url, response, service_name)

        return (
            response.json()
            if response.headers.get("content-type", "").lower().startswith("application/json")
            else {"raw": response.text[:500]}
        )

    def _store_response(self, url: str, response: Any, service_name: str) -> None:
        """Store API response in database."""
        # This would be implemented by the parent client's database access
        # For now, just a placeholder for future integration
        pass
