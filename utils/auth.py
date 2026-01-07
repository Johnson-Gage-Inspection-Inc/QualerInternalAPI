"""Authentication utilities for Qualer API access."""

import os
from typing import Optional
import requests
from time import sleep
from getpass import getpass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
import re

from persistence.storage import StorageAdapter, PostgresRawStorage

load_dotenv()


class QualerAPIFetcher:
    """
    Context manager for authenticating with Qualer and extracting cookies.

    Uses Selenium for browser automation to handle login, then provides an
    authenticated requests.Session for API calls.
    """

    def __init__(
        self,
        db_url: Optional[str] = None,
        storage: Optional[StorageAdapter] = None,
        headless: bool = True,
        username: Optional[str] = None,
        password: Optional[str] = None,
        login_wait_time: float = 5.0,
    ):
        """
        Initialize Qualer API authenticator with optional storage.

        Args:
            db_url: (Optional) PostgreSQL connection string. If provided, creates PostgresRawStorage.
                    If omitted and no storage provided, DB operations will be disabled.
            storage: (Optional) Custom storage adapter (PostgresRawStorage, CSVStorage, etc.)
                     Overrides db_url if both provided.
            headless: Run Selenium in headless mode (default: True)
            username: Qualer username (reads from QUALER_EMAIL env var if not provided)
            password: Qualer password (reads from QUALER_PASSWORD env var if not provided)
            login_wait_time: Seconds to wait after login for page to load
                            (configurable via QUALER_LOGIN_WAIT_TIME env var)

        Examples:
            # With database (backward compatible)
            with QualerAPIFetcher(db_url="postgresql://...") as api:
                api.fetch_and_store(url, "ClientInformation")

            # With CSV storage (ad-hoc analysis)
            from persistence import CSVStorage
            with QualerAPIFetcher(storage=CSVStorage("data/")) as api:
                api.fetch_and_store(url, "ClientInformation")

            # Without storage (pure API client)
            with QualerAPIFetcher() as api:
                response = api.session.get(url)
        """
        # Storage setup
        self.storage: Optional[StorageAdapter]
        if storage:
            self.storage = storage
        elif db_url:
            self.storage = PostgresRawStorage(db_url)
        else:
            # Try environment variable for backward compatibility
            db_url = os.getenv("DB_URL")
            self.storage = PostgresRawStorage(db_url) if db_url else None

        # Authentication setup
        self.username = username or os.getenv("QUALER_EMAIL")
        self.password = password or os.getenv("QUALER_PASSWORD")
        self.driver = None
        self.headless = headless
        self.session = None
        self.login_wait_time = float(os.getenv("QUALER_LOGIN_WAIT_TIME", login_wait_time))

    def __enter__(self):
        """
        Called upon entering the `with` block. Initializes Selenium driver,
        logs in to Qualer, and builds a requests.Session from Selenium's cookies.
        """
        self._init_driver()
        self._login()
        self._build_requests_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Called upon exiting the `with` block. Cleans up resources."""
        if self.driver:
            self.driver.quit()
            self.driver = None
        if self.storage:
            self.storage.close()

    def _init_driver(self):
        """Initialize Chrome WebDriver."""
        chrome_options = webdriver.ChromeOptions()
        if self.headless:
            chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)

    def _login(self):
        """
        Logs in to Qualer via Selenium.

        If username/password weren't provided, prompts user for credentials.
        """
        assert self.driver is not None
        self.driver.get("https://jgiquality.qualer.com/login")

        # If username/password weren't supplied or found in env vars, prompt:
        if not self.username:
            self.username = input("Qualer Username: ")
        if not self.password:
            self.password = getpass("Qualer Password: ")

        # By now, username and password must be set
        assert self.username is not None
        assert self.password is not None

        self.driver.find_element(By.ID, "Email").send_keys(self.username)
        self.driver.find_element(By.ID, "Password").send_keys(self.password + Keys.RETURN)

        sleep(self.login_wait_time)  # Wait for page load
        if "login" in self.driver.current_url.lower():
            raise RuntimeError("Login failed. Check your credentials.")

    def _build_requests_session(self):
        """Copy Selenium's cookies into a requests.Session."""
        self.session = requests.Session()
        assert self.driver is not None
        for cookie in self.driver.get_cookies():
            self.session.cookies.set(cookie["name"], cookie["value"])

    def get_headers(self, referer: Optional[str] = None, **overrides) -> dict:
        """
        Get standard Qualer API headers with optional customization.

        Provides sensible defaults for common Qualer API calls. All headers
        are standard except referer, which must be set based on current context.

        Args:
            referer: (Optional) Referer URL. If not provided, uses current driver URL
                     or falls back to Qualer base URL.
            **overrides: Additional headers to override or add
                        (keys with underscores are converted to hyphens)

        Returns:
            Dictionary of HTTP headers ready for requests

        Example:
            >>> headers = api.get_headers(referer="https://jgiquality.qualer.com/clients")
            >>> response = api.session.post(url, data=payload, headers=headers)
        """
        # Default referer: use current driver URL or fall back to base
        if referer is None:
            if self.driver:
                referer = self.driver.current_url
            else:
                referer = "https://jgiquality.qualer.com/"

        # Standard headers for Qualer API requests
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache, must-revalidate",
            "pragma": "no-cache",
            "referer": referer,
        }

        # Convert underscore keys to hyphenated headers
        for key, value in overrides.items():
            header_name = key.replace("_", "-")
            headers[header_name] = value

        return headers

    def run_sql(self, sql_query, params=None):
        """
        Execute a SQL query and return all rows.

        Note: Only works with PostgresRawStorage. For other storage backends,
        access the storage adapter directly.
        """
        if not self.storage:
            raise RuntimeError(
                "No storage configured. Provide db_url or storage adapter to use SQL."
            )
        if not isinstance(self.storage, PostgresRawStorage):
            raise RuntimeError(
                f"run_sql() only works with PostgresRawStorage, got {type(self.storage).__name__}"
            )
        return self.storage.run_sql(sql_query, params)

    def fetch_and_store(self, url, service, method="GET"):
        """
        Fetch URL and store response using configured storage adapter.

        Combines fetch() (Selenium-based with <pre> tag extraction) and store()
        to fetch HTML-wrapped JSON and store it in the configured backend.

        Args:
            url: Endpoint URL to fetch
            service: Service name for storage organization
            method: HTTP method for logging (default: "GET")

        Raises:
            RuntimeError: If driver, session, or storage not initialized
        """
        if not self.storage:
            raise RuntimeError(
                "No storage configured. Provide db_url or storage adapter to use fetch_and_store."
            )

        # Use fetch() to handle Selenium navigation and <pre> tag extraction
        response = self.fetch(url)
        # Use store() to save the response via the configured storage adapter
        self.store(url, service, method, response)

    def store(self, url, service, method, response):
        """
        Store a requests.Response object using configured storage adapter.

        This is a convenience method for storing responses obtained via
        api.session.get() or api.fetch() methods.
        """
        if not self.storage:
            raise RuntimeError(
                "No storage configured. Provide db_url or storage adapter to use store."
            )

        if not response.text:
            raise RuntimeError("Response body is empty. Did the request fail?")

        if not response.ok:
            raise RuntimeError(f"Request to {url} failed with status code {response.status_code}")

        self.storage.store_response(
            url=url,
            service=service,
            method=method,
            request_headers=dict(response.request.headers),
            response_body=response.text,
            response_headers=dict(response.headers),
        )

    def get(
        self, url: str, params: Optional[dict] = None, referer: Optional[str] = None, **kwargs
    ) -> requests.Response:
        """
        GET request with standard Qualer headers pre-configured.

        Automatically includes common headers (accept, cache-control, etc.).
        Simplifies endpoint implementations.

        Args:
            url: Endpoint URL
            params: (Optional) Query parameters dictionary
            referer: (Optional) Referer URL for the request
            **kwargs: Additional arguments passed to session.get() (timeout, etc.)

        Returns:
            requests.Response object

        Raises:
            RuntimeError: If session not initialized
            requests.HTTPError: If response status indicates error

        Example:
            >>> response = api.get(
            ...     "https://jgiquality.qualer.com/ClientDashboard/Clients_Read",
            ...     params={"sort": "Name-asc", "page": 1, ...},
            ...     referer="https://jgiquality.qualer.com/clients",
            ...     timeout=30
            ... )
            >>> data = response.json()
        """
        if not self.session:
            raise RuntimeError("No valid session. Did login succeed?")

        # Get standard headers
        headers = self.get_headers(
            referer=referer,
            x_requested_with="XMLHttpRequest",
        )

        # Make request with standard headers
        response = self.session.get(url, params=params, headers=headers, **kwargs)
        response.raise_for_status()
        return response

    def post(
        self,
        url: str,
        data: Optional[dict] = None,
        referer: Optional[str] = None,
        **kwargs,
    ) -> requests.Response:
        """
        POST request with standard Qualer headers pre-configured.

        Automatically includes common headers (accept, cache-control, etc.) plus
        x-requested-with and content-type headers appropriate for form data submission.

        Args:
            url: Endpoint URL
            data: (Optional) Form data dictionary to POST
            referer: (Optional) Referer URL for the request
            **kwargs: Additional arguments passed to session.post() (timeout, etc.)

        Returns:
            requests.Response object

        Raises:
            RuntimeError: If session not initialized
            requests.HTTPError: If response status indicates error

        Example:
            >>> response = api.post(
            ...     "https://jgiquality.qualer.com/ClientDashboard/Clients_Read",
            ...     data={"sort": "Name-asc", "page": 1, ...},
            ...     referer="https://jgiquality.qualer.com/clients",
            ...     timeout=30
            ... )
            >>> client_data = response.json()
        """
        if not self.session:
            raise RuntimeError("No valid session. Did login succeed?")

        # Get standard headers with POST-specific additions
        headers = self.get_headers(
            referer=referer,
            x_requested_with="XMLHttpRequest",
            content_type="application/x-www-form-urlencoded; charset=UTF-8",
        )

        # Make request with standard headers
        response = self.session.post(url, data=data, headers=headers, **kwargs)
        response.raise_for_status()
        return response

    def fetch(self, url):
        """
        Fetch URL using authenticated session with Qualer's HTML-wrapped JSON handling.

        Qualer wraps JSON responses in HTML: <html><body><pre>{json}</pre></body></html>
        This method extracts the JSON from the <pre> tag using Selenium.

        Args:
            url: Endpoint URL to fetch

        Returns:
            requests.Response object with actual JSON body (not HTML-wrapped)

        Raises:
            RuntimeError: If session not initialized or <pre> tag not found in response

        Example:
            >>> response = api.fetch("https://jgiquality.qualer.com/work/Uncertainties/...")
            >>> data = response.json()
        """
        if not self.session:
            raise RuntimeError("No valid session. Did login succeed?")
        r = self.session.get(url)
        r.raise_for_status()
        # Selenium is needed to get the response body
        assert self.driver is not None
        self.driver.get(url)
        actual_body = self.driver.page_source
        soup = BeautifulSoup(actual_body, "html.parser")
        pre = soup.find("pre")
        if not pre:
            raise RuntimeError("Couldn't find <pre> tag in response body")
        parsed_data = json.loads(pre.text.strip())
        # Build a new response object with the actual body
        new_response = requests.Response()
        new_response.status_code = 200
        new_response._content = json.dumps(parsed_data).encode("utf-8")
        new_response.url = url
        new_response.headers = r.headers
        new_response.request = r.request
        return new_response

    def extract_csrf_token(self, html: str) -> str:
        """
        Extract CSRF token from HTML page.

        Searches for __RequestVerificationToken in hidden input fields.

        Args:
            html: HTML content to search

        Returns:
            The CSRF token value

        Raises:
            ValueError: If token cannot be found in HTML
        """
        # Look for __RequestVerificationToken in hidden input
        # Pattern allows for attributes like type="hidden" between name and value
        match = re.search(r'name="__RequestVerificationToken"[^>]*value="([^"]+)"', html)
        if match:
            return match.group(1)

        # Try alternate pattern (value before name)
        match = re.search(r'value="([^"]+)"[^>]*name="__RequestVerificationToken"', html)
        if match:
            return match.group(1)

        # Debug: print a snippet of the HTML
        print("DEBUG: Could not find token. Checking page structure...")
        if "__RequestVerificationToken" in html:
            # Find context around the token
            idx = html.find("__RequestVerificationToken")
            snippet = html[max(0, idx - 100) : idx + 200]
            print(f"Found token reference at:\n{snippet}\n")
        else:
            print("Token name not found in HTML at all")
            # Print first 2000 chars to see structure
            print(f"HTML snippet:\n{html[:2000]}\n")

        raise ValueError("Could not find CSRF token in page")
