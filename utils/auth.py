"""Authentication utilities for Qualer API access."""

import os
from typing import Optional
import requests
from time import sleep
from getpass import getpass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from sqlalchemy import create_engine, text
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
import re

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
        headless: bool = True,
        username: Optional[str] = None,
        password: Optional[str] = None,
        login_wait_time: float = 5.0,
    ):
        """
        db_url: Full connection string to your Postgres database
        username, password: Optionally provide credentials for Qualer. If not
                           supplied, environment variables or interactive prompts
                           will be used.
        login_wait_time: Seconds to wait after login for page to load
                        (configurable via QUALER_LOGIN_WAIT_TIME env var)
        """
        if not db_url:
            db_url = os.getenv("DB_URL")
        if not db_url:
            raise EnvironmentError("DB_URL environment variable is not set")
        self.db_url = db_url
        self.username = username or os.getenv("QUALER_USERNAME")
        self.password = password or os.getenv("QUALER_PASSWORD")
        self.driver = None
        self.headless = headless
        self.session = None
        self.engine = None
        self.login_wait_time = float(os.getenv("QUALER_LOGIN_WAIT_TIME", login_wait_time))

    def __enter__(self):
        """
        Called upon entering the `with` block. Creates a DB engine, Selenium
        driver, logs in to Qualer, and builds a requests.Session from
        Selenium's cookies.
        """
        self.engine = create_engine(self.db_url)
        self._init_driver()
        self._login()
        self._build_requests_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Called upon exiting the `with` block. Cleans up resources."""
        if self.driver:
            self.driver.quit()
            self.driver = None
        if self.engine:
            self.engine.dispose()
            self.engine = None

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

    def run_sql(self, sql_query, params=None):
        """Execute a SQL query and return all rows."""
        assert self.engine is not None
        with self.engine.connect() as conn:
            result = conn.execute(text(sql_query), params or {})
            return result.fetchall()

    def fetch_and_store(self, url, service, method="GET"):
        """Fetch URL and insert response into datadump table."""
        if not self.driver or not self.session:
            raise RuntimeError("Driver or session not initialized")

        # First, get response headers from requests to check Content-Type
        r = self.session.get(url)
        # Handle HTTP errors early to avoid inserting error pages into the database.
        # Skip 403s gracefully in bulk operations, per project conventions.
        if r.status_code == 403:
            print(f"Warning: 403 Forbidden when accessing {url}. Skipping.")
            return
        r.raise_for_status()
        content_type = r.headers.get("Content-Type", "").lower()

        # Use Selenium to get the actual response body (handles JavaScript-rendered content)
        self.driver.get(url)
        response_body = self.driver.page_source

        # If JSON response, try to extract from <pre> tag; otherwise store raw HTML
        if content_type.startswith("application/json") or "json" in content_type:
            soup = BeautifulSoup(response_body, "html.parser")
            if pre := soup.find("pre"):  # HACK: What's the significance of <pre> here?
                response_body = pre.text.strip()

        # Store response to database
        assert self.engine is not None
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO datadump (url, service, method, request_header, response_body, response_header)
                    VALUES (:url, :service, :method, :req_headers, :res_body, :res_headers)
                    ON CONFLICT (url, service, method) DO NOTHING
                    """
                ),
                {
                    "url": url,
                    "service": service,
                    "method": method,
                    "req_headers": dict(r.request.headers) if r.request else {},
                    "res_body": response_body,
                    "res_headers": dict(r.headers),
                },
            )

    def store(self, url, service, method, response):
        """Store request/response in database."""
        if not response.text:
            raise RuntimeError("Response body is empty. Did the request fail?")
        if response.ok:
            req_headers = dict(response.request.headers)
            res_headers = dict(response.headers)
            assert self.engine is not None
            with self.engine.begin() as conn:
                conn.execute(
                    text(
                        """
                        INSERT INTO datadump (
                            service, method, url,
                            request_header, request_body,
                            response_header, response_body
                        )
                        VALUES (
                            :service, :method, :url,
                            :req_headers, NULL,
                            :res_headers, :res_body
                        )
                        ON CONFLICT DO NOTHING;
                    """
                    ),
                    {
                        "service": service,
                        "method": method,
                        "url": url,
                        "req_headers": req_headers,
                        "res_headers": res_headers,
                        "res_body": response.text,
                    },
                )
        else:
            raise RuntimeError(f"Request to {url} failed with status code {response.status_code}")

    def fetch(self, url):
        """Fetch URL using authenticated session."""
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
