"""Unified Qualer API Client - wraps all endpoints with a clean interface."""

from typing import Optional

from utils.auth import QualerAPIFetcher
from qualer_internal_sdk.endpoints import client_dashboard, client
from qualer_internal_sdk.endpoints.service.service_groups import ServiceGroupsEndpoint
from qualer_internal_sdk.endpoints.uncertainty.uncertainty_parameters import (
    UncertaintyParametersEndpoint,
)
from qualer_internal_sdk.endpoints.uncertainty.uncertainty_modal import UncertaintyModalEndpoint


class ClientDashboardEndpoint:
    """Namespace for ClientDashboard endpoints."""

    def __init__(self, api: QualerAPIFetcher):
        self.api = api

    def clients_read(self, page_size: int = 1000000) -> dict:
        """
        Fetch all clients from Qualer.

        Args:
            page_size: Number of results to fetch per page

        Returns:
            Dictionary containing client data
        """
        return client_dashboard.clients_read(page_size)


class ClientEndpoint:
    """Namespace for Client endpoints."""

    def __init__(self, api: QualerAPIFetcher):
        self.api = api

    def fetch_and_store(self, client_ids: list) -> None:
        """
        Fetch and store client information for multiple clients.

        Args:
            client_ids: List of client IDs to fetch
        """
        client.fetch_client_information(client_ids, self.api)


class ServiceEndpoint:
    """Namespace for Service endpoints."""

    def __init__(self, api: QualerAPIFetcher):
        self.api = api
        self.service_groups: Optional[ServiceGroupsEndpoint] = None

    def _initialize(self):
        """Initialize endpoints after session is available."""
        self.service_groups = ServiceGroupsEndpoint(self.api.session, self.api.driver)

    def get_service_groups(self, service_order_item_id: int) -> dict:
        """Fetch service groups for a service order item."""
        if self.service_groups is None:
            raise RuntimeError("Service endpoint not initialized - use within context manager")
        return self.service_groups.get_service_groups(service_order_item_id)


class UncertaintyEndpoint:
    """Namespace for Uncertainty endpoints."""

    def __init__(self, api: QualerAPIFetcher):
        self.api = api
        self.parameters: Optional[UncertaintyParametersEndpoint] = None
        self.modal: Optional[UncertaintyModalEndpoint] = None

    def _initialize(self):
        """Initialize endpoints after session is available."""
        self.parameters = UncertaintyParametersEndpoint(self.api.session, self.api.driver)
        self.modal = UncertaintyModalEndpoint(self.api.session, self.api.driver)

    def get_parameters(self, measurement_id: int, uncertainty_budget_id: int) -> dict:
        """Fetch uncertainty parameters."""
        if self.parameters is None:
            raise RuntimeError("Uncertainty endpoint not initialized - use within context manager")
        return self.parameters.get_parameters(measurement_id, uncertainty_budget_id)

    def get_modal(self, measurement_id: int, batch_id: int) -> dict:
        """Fetch uncertainty modal."""
        if self.modal is None:
            raise RuntimeError("Uncertainty endpoint not initialized - use within context manager")
        return self.modal.get_modal(measurement_id, batch_id)


class QualerClient:
    """
    Unified Qualer API Client.

    Provides a clean, intuitive interface for accessing all Qualer endpoints.
    Works as a context manager to handle authentication and cleanup.

    Example:
        ```python
        with QualerClient() as client:
            # Fetch all clients
            clients = client.client_dashboard.clients_read()

            # Fetch and store client info
            client_ids = [c["Id"] for c in clients["data"]]
            client.client.fetch_and_store(client_ids)
        ```
    """

    def __init__(
        self,
        headless: bool = True,
        username: Optional[str] = None,
        password: Optional[str] = None,
        login_wait_time: float = 5.0,
    ):
        """
        Initialize Qualer API Client.

        Args:
            headless: Run Selenium in headless mode (default: True)
            username: Qualer username (reads from env var if not provided)
            password: Qualer password (reads from env var if not provided)
            login_wait_time: Seconds to wait after login (configurable via env var)
        """
        self.headless = headless
        self.username = username
        self.password = password
        self.login_wait_time = login_wait_time
        self._api = None

        # Endpoint namespaces
        self.client_dashboard: Optional[ClientDashboardEndpoint] = None
        self.client: Optional[ClientEndpoint] = None
        self.service: Optional[ServiceEndpoint] = None
        self.uncertainty: Optional[UncertaintyEndpoint] = None

    def __enter__(self):
        """Enter context manager - initialize API and endpoints."""
        self._api = QualerAPIFetcher(
            headless=self.headless,
            username=self.username,
            password=self.password,
            login_wait_time=self.login_wait_time,
        )
        self._api.__enter__()

        # Initialize endpoint namespaces
        self.client_dashboard = ClientDashboardEndpoint(self._api)
        self.client = ClientEndpoint(self._api)
        self.service = ServiceEndpoint(self._api)
        self.uncertainty = UncertaintyEndpoint(self._api)

        # Initialize sub-endpoints after session is available
        self.service._initialize()
        self.uncertainty._initialize()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager - cleanup API resources."""
        if self._api:
            self._api.__exit__(exc_type, exc_val, exc_tb)
        return False
