"""Uncertainty modal endpoint module for Qualer API.

Provides methods to fetch uncertainty modal data.
"""

from typing import Any, Dict, List, Optional, Tuple
from requests import Session
from selenium.webdriver.remote.webdriver import WebDriver
from tqdm import tqdm


class UncertaintyModalEndpoint:
    """Encapsulates uncertainty modal API endpoint operations."""

    def __init__(self, session: Optional[Session], driver: Optional[WebDriver] = None):
        """Initialize the UncertaintyModalEndpoint.

        Args:
            session: Authenticated requests.Session object
            driver: Optional Selenium WebDriver for JavaScript-rendered content
        """
        self.session = session
        self.driver = driver

    def fetch_for_measurements(
        self,
        measurement_batches: List[Tuple[int, int]],
        service_name: str = "UncertaintyModal",
    ) -> Dict[Tuple[int, int], Any]:
        """Fetch uncertainty modals for multiple measurements and batches.

        Args:
            measurement_batches: List of (measurement_id, batch_id) tuples
            service_name: Service name for database storage

        Returns:
            Dictionary mapping (measurement_id, batch_id) tuples to API responses

        Example:
            >>> endpoint = UncertaintyModalEndpoint(session)
            >>> results = endpoint.fetch_for_measurements([(1, 100), (2, 200)])
            >>> print(results[(1, 100)])
        """
        results = {}

        for measurement_id, batch_id in tqdm(
            measurement_batches, desc="Fetching uncertainty modals"
        ):
            try:
                result = self.get_modal(measurement_id, batch_id, service_name)
                results[(measurement_id, batch_id)] = result
            except Exception as e:
                print(
                    f"Warning: Failed to fetch modal for measurement {measurement_id}, "
                    f"batch {batch_id}: {e}"
                )
                results[(measurement_id, batch_id)] = {"error": str(e)}

        return results

    def get_modal(
        self,
        measurement_id: int,
        batch_id: int,
        service_name: str = "UncertaintyModal",
    ) -> Dict[str, Any]:
        """Fetch uncertainty modal for a specific measurement and batch.

        Args:
            measurement_id: Measurement ID
            batch_id: Measurement batch ID
            service_name: Service name for database storage

        Returns:
            API response as dictionary

        Raises:
            RuntimeError: If session is not available
            requests.HTTPError: On HTTP errors
        """
        if not self.session:
            raise RuntimeError("Session not available")

        url = (
            "https://jgiquality.qualer.com/work/Uncertainties/UncertaintyModal?"
            f"measurementId={measurement_id}&MeasurementBatchId={batch_id}"
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
        # Placeholder for future database integration
        pass
