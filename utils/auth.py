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

    Authentication Patterns:
    -----------------------

    🌐 HTTP-Based Methods (use when possible):
        - get()  → Standard HTTP GET with requests.Session
        - post() → Standard HTTP POST with requests.Session
        - fetch() → HTTP GET with <pre> tag extraction
        ✅ Use for: Standard REST APIs that accept HTTP requests
        ❌ Fails with: 401 errors on some Qualer internal endpoints

    🖥️ Browser-Based Methods (use when HTTP fails):
        - fetch_via_browser() → JavaScript fetch() executed in browser
        ✅ Use for: Qualer internal APIs that validate browser context
        ⚠️ Slower but bypasses authentication validation issues
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
        self.driver: Optional[webdriver.Chrome] = None
        self.headless = headless
        self.session: Optional[requests.Session] = None
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
            self.driver = None  # type: ignore
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
        include_csrf: bool = True,
        **kwargs,
    ) -> requests.Response:
        """
        POST request with standard Qualer headers pre-configured.

        Automatically includes common headers (accept, cache-control, etc.) plus
        x-requested-with and content-type headers appropriate for form data submission.

        Optionally auto-injects CSRF token if needed (default: True).

        Args:
            url: Endpoint URL
            data: (Optional) Form data dictionary to POST
            referer: (Optional) Referer URL for the request
            include_csrf: (Optional) Automatically extract and inject CSRF token if missing
                         from data dict and driver has loaded page (default: True)
            **kwargs: Additional arguments passed to session.post() (timeout, etc.)

        Returns:
            requests.Response object

        Raises:
            RuntimeError: If session not initialized
            requests.HTTPError: If response status indicates error

        Example:
            >>> # CSRF token automatically added if needed
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

        # Auto-inject CSRF token if requested and not already in data
        if data is None:
            data = {}

        if include_csrf and "__RequestVerificationToken" not in data:
            if self.driver and self.driver.current_url:
                try:
                    csrf_token = self.extract_csrf_token(self.driver.page_source)
                    data["__RequestVerificationToken"] = csrf_token
                except ValueError:
                    # Token not found - endpoint might not require it
                    pass

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

    def _generate_browser_fetch_js(self, method: str, url: str, body: Optional[str] = None) -> str:
        """
        Generate JavaScript fetch code to execute in browser context.

        This JavaScript code is injected into the authenticated browser session
        and executed via execute_async_script(). The browser's authentication
        context is what makes these requests succeed (pure HTTP requests fail).

        Security Note: url and body are URL-encoded by the caller (urlencode)
        before being passed here, so special characters are already escaped.
        The JavaScript string interpolation is safe because values are pre-encoded.

        Args:
            method: HTTP method ("GET" or "POST")
            url: Full URL including query string for GET (already URL-encoded)
            body: URL-encoded form data string for POST (None for GET)

        Returns:
            JavaScript code string ready for execute_async_script()
        """
        if method.upper() == "GET":
            return f"""
            var callback = arguments[arguments.length - 1];
            fetch('{url}', {{
                method: 'GET',
                headers: {{
                    'x-requested-with': 'XMLHttpRequest'
                }},
                credentials: 'include'
            }})
            .then(response => response.json())
            .then(data => callback(data))
            .catch(error => callback({{error: error.toString()}}));
            """
        else:  # POST
            return f"""
            var callback = arguments[arguments.length - 1];
            fetch('{url}', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'x-requested-with': 'XMLHttpRequest'
                }},
                body: '{body}',
                credentials: 'include'
            }})
            .then(response => {{
                if (!response.ok) {{
                    return callback({{error: 'HTTP ' + response.status + ': ' + response.statusText}});
                }}
                return response.json();
            }})
            .then(data => {{
                if (data && !data.error) {{
                    callback(data);
                }}
            }})
            .catch(error => callback({{error: error.toString()}}));
            """

    def fetch_via_browser(
        self,
        method: str,
        endpoint_path: str,
        auth_context_page: str,
        params: dict,
        include_csrf: Optional[bool] = None,
    ) -> dict:
        """
        Fetch API endpoint by executing JavaScript fetch() inside authenticated browser.

        ⚠️ BROWSER-BASED APPROACH - Use this instead of get()/post() for endpoints that:
        - Return 401 errors with pure HTTP requests (even with valid cookies/CSRF)
        - Require JavaScript execution context for authentication validation
        - Are part of Qualer's internal/undocumented API

        This method:
        1. Navigates to a page to establish auth context
        2. Generates JavaScript fetch() code
        3. Injects and executes it in the browser via Selenium
        4. Returns the parsed JSON response

        For standard REST APIs that accept HTTP requests, use get() or post() instead.

        Args:
            method: HTTP method - "GET" or "POST"
            endpoint_path: API endpoint path (e.g., "/ClientDashboard/ClientsCountView")
            auth_context_page: Page to navigate to for auth context (e.g., "/clients")
            params: Request parameters (query params for GET, form data for POST)
            include_csrf: Whether to include CSRF token (default: True for POST, False for GET)

        Returns:
            Parsed JSON response from the endpoint

        Raises:
            RuntimeError: If driver not initialized or JavaScript execution fails

        Example:
            >>> # Endpoint that requires browser context
            >>> response = api.fetch_via_browser(
            ...     method="POST",
            ...     endpoint_path="/ClientDashboard/Clients_Read",
            ...     auth_context_page="/clients",
            ...     params={"sort": "Name-asc", "page": 1},
            ... )
        """
        if not self.driver:
            raise RuntimeError("Driver not initialized")

        # Get base URL from current session
        base_url = "https://jgiquality.qualer.com"

        # Navigate to auth context page
        self.driver.get(f"{base_url}{auth_context_page}")
        sleep(3)  # Wait longer for JavaScript and AJAX to complete

        # Auto-determine CSRF inclusion if not specified
        if include_csrf is None:
            include_csrf = method.upper() == "POST"

        # Add CSRF token for POST requests
        if include_csrf and method.upper() == "POST":
            try:
                csrf_token = self.extract_csrf_token(self.driver.page_source)
                params["__RequestVerificationToken"] = csrf_token
            except ValueError:
                # Token not found - some endpoints may not require it
                # or it may be injected differently. Proceed without it.
                print("WARNING: No CSRF token found, proceeding without it...")
                pass

        # Build URL and generate JavaScript fetch code
        from urllib.parse import urlencode

        if method.upper() == "GET":
            query_string = urlencode(params)
            url = f"{base_url}{endpoint_path}?{query_string}"
            js_code = self._generate_browser_fetch_js("GET", url)
        else:  # POST
            url = f"{base_url}{endpoint_path}"
            payload = urlencode(params)
            js_code = self._generate_browser_fetch_js("POST", url, payload)

        # Execute JavaScript in browser and get result
        result = self.driver.execute_async_script(js_code)

        if isinstance(result, dict) and "error" in result:
            raise RuntimeError(f"JavaScript fetch failed: {result['error']}")

        return result
