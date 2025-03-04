import os
import requests
from time import sleep
from getpass import getpass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from sqlalchemy import create_engine, text


class QualerAPIFetcher:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.driver = None
        self.session = None

    def init_driver(self):
        if self.driver is not None:
            return
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)

    def login(self, username=None, password=None):
        self.init_driver()
        self.driver.get("https://jgiquality.qualer.com/login")
        username = username or os.getenv("QUALER_USERNAME") or input("Qualer Username: ")
        password = password or os.getenv("QUALER_PASSWORD") or getpass("Qualer Password: ")
        self.driver.find_element(By.ID, "Email").send_keys(username)
        self.driver.find_element(By.ID, "Password").send_keys(password + Keys.RETURN)
        sleep(5)
        if "login" in self.driver.current_url.lower():
            raise RuntimeError("Login failed. Check credentials.")
        self._build_requests_session()

    def _build_requests_session(self):
        self.session = requests.Session()
        for cookie in self.driver.get_cookies():
            self.session.cookies.set(cookie["name"], cookie["value"])

    def fetch_and_store(self, url, service="QualerAPI", method="GET"):
        if not self.session:
            raise RuntimeError("Not logged in. Call login() first.")

        response = self.session.get(url)
        if response.ok:
            req_headers = dict(response.request.headers)
            res_headers = dict(response.headers)
            with self.engine.connect() as conn:
                conn.execute(
                    text("""
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
                    """),
                    service=service,
                    method=method,
                    url=url,
                    req_headers=req_headers,
                    res_headers=res_headers,
                    res_body=response.text
                )
        else:
            raise RuntimeError(f"Request failed with status code {response.status_code}")

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None


# Example usage:
if __name__ == "__main__":
    # Point to your actual Postgres server
    db_url = "postgresql://postgres:postgres@192.168.1.177:5432/qualer"

    fetcher = QualerAPIFetcher(db_url)
    fetcher.login()  # Will prompt or use environment variables
    try:
        test_url = "https://jgiquality.qualer.com/work/Uncertainties/UncertaintyModal?measurementId=89052138&lastMeasurementBatchId=4202634"
        fetcher.fetch_and_store(test_url)
        print("Data inserted into datadump.")
    finally:
        fetcher.close()
