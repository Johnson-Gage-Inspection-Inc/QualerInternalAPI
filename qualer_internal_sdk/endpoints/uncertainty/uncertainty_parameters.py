"""Uncertainty parameters endpoint module for Qualer API.

Provides methods to fetch uncertainty parameter data.
"""

from typing import Any, Dict, List, Optional, Tuple
from requests import Session
from selenium.webdriver.remote.webdriver import WebDriver
from tqdm import tqdm


class UncertaintyParametersEndpoint:
    """Encapsulates uncertainty parameters API endpoint operations."""

    def __init__(self, session: Session, driver: Optional[WebDriver] = None):
        """Initialize the UncertaintyParametersEndpoint.

        Args:
            session: Authenticated requests.Session object
            driver: Optional Selenium WebDriver for JavaScript-rendered content
        """
        self.session = session
        self.driver = driver

    def fetch_for_measurements(
        self,
        measurement_ids: List[int],
        uncertainty_budget_ids: List[int],
        service_name: str = "UncertaintyParameters",
    ) -> Dict[Tuple[int, int], Any]:
        """Fetch uncertainty parameters for all combinations of measurements and budgets.

        Args:
            measurement_ids: List of measurement IDs
            uncertainty_budget_ids: List of uncertainty budget IDs
            service_name: Service name for database storage

        Returns:
            Dictionary mapping (measurement_id, budget_id) tuples to API responses

        Example:
            >>> endpoint = UncertaintyParametersEndpoint(session)
            >>> results = endpoint.fetch_for_measurements([1, 2], [10, 20])
            >>> print(results[(1, 10)])
        """
        results = {}
        total_combinations = len(measurement_ids) * len(uncertainty_budget_ids)

        with tqdm(total=total_combinations, desc="Fetching uncertainty parameters") as pbar:
            for measurement_id in measurement_ids:
                for budget_id in uncertainty_budget_ids:
                    try:
                        result = self.get_parameters(measurement_id, budget_id, service_name)
                        results[(measurement_id, budget_id)] = result
                    except Exception as e:
                        print(
                            f"Warning: Failed to fetch parameters for measurement {measurement_id}, "
                            f"budget {budget_id}: {e}"
                        )
                        results[(measurement_id, budget_id)] = {"error": str(e)}
                    pbar.update(1)

        return results

    def get_parameters(
        self,
        measurement_id: int,
        uncertainty_budget_id: int,
        service_name: str = "UncertaintyParameters",
    ) -> Dict[str, Any]:
        """Fetch uncertainty parameters for a specific measurement and budget.

        Args:
            measurement_id: Measurement ID
            uncertainty_budget_id: Uncertainty budget ID
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
            "https://jgiquality.qualer.com/work/Uncertainties/UncertaintyParameters?"
            f"measurementId={measurement_id}&uncertaintyBudgetId={uncertainty_budget_id}"
        )

        response = self.session.get(url, timeout=30)
        response.raise_for_status()

        # Store in database if driver is available
        if self.driver:
            self._store_response(url, response, service_name)

        return response.json() if response.headers.get("content-type", "").lower().startswith("application/json") else {"raw": response.text[:500]}

    def _store_response(self, url: str, response: Any, service_name: str) -> None:
        """Store API response in database."""
        # Placeholder for future database integration
        pass
