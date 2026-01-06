"""Authentication utilities for Qualer API access."""

import os
import requests
from time import sleep
from getpass import getpass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from sqlalchemy import create_engine, text
from bs4 import BeautifulSoup
import json


env_file = "C:/Users/JGI/Jeff H/Escape Dantes Inferno/QualerInternalAPI/.env"
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            key, value = line.strip().split("=")
            os.environ[key] = value


class QualerAPIFetcher:
    """
    Context manager for authenticating with Qualer and extracting cookies.

    Uses Selenium for browser automation to handle login, then provides an
    authenticated requests.Session for API calls.
    """

    def __init__(
        self,
        db_url="postgresql://postgres:postgres@192.168.1.177:5432/qualer",
        headless=True,
        username=None,
        password=None,
    ):
        """
        db_url: Full connection string to your Postgres database
        username, password: Optionally provide credentials for Qualer. If not
                           supplied, environment variables or interactive prompts
                           will be used.
        """
        self.db_url = db_url
        self.username = username or os.getenv("QUALER_USERNAME")
        self.password = password or os.getenv("QUALER_PASSWORD")
        self.driver = None
        self.headless = headless
        self.session = None
        self.engine = None

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

        self.driver.find_element(By.ID, "Email").send_keys(self.username)
        self.driver.find_element(By.ID, "Password").send_keys(
            self.password + Keys.RETURN
        )

        sleep(5)  # Let the page load. Increase if site is slow.
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
        response = self.fetch(url)
        self.store(url, service, method, response)

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
            raise RuntimeError(
                f"Request to {url} failed with status code {response.status_code}"
            )

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
