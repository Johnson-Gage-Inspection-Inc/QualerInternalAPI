"""Unified Qualer API Client - wraps all endpoints with a clean interface."""

from typing import Optional

from utils.auth import QualerAPIFetcher
from qualer_internal_sdk.endpoints import client_dashboard, client


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
        client.client_information.fetch_and_store(client_ids, self.api)


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
        self.client_dashboard: ClientDashboardEndpoint
        self.client: ClientEndpoint

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

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager - cleanup API resources."""
        if self._api:
            self._api.__exit__(exc_type, exc_val, exc_tb)
        return False
