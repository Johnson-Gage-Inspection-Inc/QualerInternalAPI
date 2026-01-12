"""Tests for HTTP-first authentication pattern with browser fallback."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from qualer_internal_sdk.endpoints.client_dashboard.clients_read import clients_read
from utils.auth import QualerAPIFetcher


@pytest.fixture
def mock_qualer_api_fetcher():
    """Create a mock QualerAPIFetcher."""
    fetcher = Mock()
    fetcher.__enter__ = Mock(return_value=fetcher)
    fetcher.__exit__ = Mock(return_value=False)
    fetcher.driver = Mock()
    fetcher.session = Mock()
    return fetcher


@pytest.fixture
def mock_driver():
    """Create a mock Selenium driver."""
    driver = Mock()
    driver.current_url = "https://jgiquality.qualer.com/clients"
    driver.page_source = """
        <html>
            <form id="clientsForm">
                <input name="__RequestVerificationToken" value="test_csrf_token" />
            </form>
        </html>
    """
    return driver


class TestClientsReadHTTPFirst:
    """Test cases for clients_read HTTP-first authentication pattern."""

    @patch("utils.auth.QualerAPIFetcher")
    def test_http_post_success(self, mock_fetcher_class, mock_qualer_api_fetcher, mock_driver):
        """Test successful HTTP POST without fallback."""
        # Setup
        mock_fetcher_class.return_value = mock_qualer_api_fetcher
        mock_qualer_api_fetcher.driver = mock_driver
        mock_qualer_api_fetcher.extract_csrf_token.return_value = "test_csrf_token"
        mock_qualer_api_fetcher.get_headers.return_value = {
            "referer": "https://jgiquality.qualer.com/clients",
            "x-requested-with": "XMLHttpRequest",
        }

        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Data": [
                {
                    "ClientID": 1,
                    "ClientCompanyName": "Test Company",
                    "ClientAccountNumber": "ACC001",
                }
            ],
            "Total": 1,
        }
        mock_qualer_api_fetcher.session.post.return_value = mock_response

        # Execute
        result = clients_read(page_size=10)

        # Verify
        assert result["Data"][0]["ClientCompanyName"] == "Test Company"
        assert result["Total"] == 1
        mock_qualer_api_fetcher.session.post.assert_called_once()
        mock_qualer_api_fetcher.fetch_via_browser.assert_not_called()

    @patch("utils.auth.QualerAPIFetcher")
    def test_http_post_fallback_on_error(
        self, mock_fetcher_class, mock_qualer_api_fetcher, mock_driver
    ):
        """Test fallback to browser-based fetch when HTTP POST fails."""
        # Setup
        mock_fetcher_class.return_value = mock_qualer_api_fetcher
        mock_qualer_api_fetcher.driver = mock_driver
        mock_qualer_api_fetcher.extract_csrf_token.return_value = "test_csrf_token"
        mock_qualer_api_fetcher.get_headers.return_value = {
            "referer": "https://jgiquality.qualer.com/clients"
        }

        # Mock failed HTTP response
        mock_qualer_api_fetcher.session.post.side_effect = Exception("Connection error")

        # Mock browser-based fallback
        mock_qualer_api_fetcher.fetch_via_browser.return_value = {
            "Data": [{"ClientID": 1, "ClientCompanyName": "Fallback Company"}],
            "Total": 1,
        }

        # Execute
        result = clients_read(page_size=10)

        # Verify fallback was used
        assert result["Data"][0]["ClientCompanyName"] == "Fallback Company"
        mock_qualer_api_fetcher.fetch_via_browser.assert_called_once()

    @patch("utils.auth.QualerAPIFetcher")
    def test_csrf_token_extraction_failure(
        self, mock_fetcher_class, mock_qualer_api_fetcher, mock_driver
    ):
        """Test fallback when CSRF token extraction fails."""
        # Setup
        mock_fetcher_class.return_value = mock_qualer_api_fetcher
        mock_qualer_api_fetcher.driver = mock_driver
        mock_qualer_api_fetcher.extract_csrf_token.side_effect = ValueError(
            "Token not found in page"
        )

        # Mock browser-based fallback
        mock_qualer_api_fetcher.fetch_via_browser.return_value = {
            "Data": [{"ClientID": 1}],
            "Total": 1,
        }

        # Execute
        result = clients_read(page_size=10)

        # Verify that browser fetch was used directly without HTTP attempt
        assert result["Total"] == 1
        mock_qualer_api_fetcher.fetch_via_browser.assert_called_once()
        mock_qualer_api_fetcher.session.post.assert_not_called()

    @patch("utils.auth.QualerAPIFetcher")
    def test_http_post_non_200_status(
        self, mock_fetcher_class, mock_qualer_api_fetcher, mock_driver
    ):
        """Test fallback when HTTP POST returns non-200 status."""
        # Setup
        mock_fetcher_class.return_value = mock_qualer_api_fetcher
        mock_qualer_api_fetcher.driver = mock_driver
        mock_qualer_api_fetcher.extract_csrf_token.return_value = "test_csrf_token"
        mock_qualer_api_fetcher.get_headers.return_value = {}

        # Mock 403 response (permission denied)
        mock_response = Mock()
        mock_response.status_code = 403
        mock_qualer_api_fetcher.session.post.return_value = mock_response

        # Mock browser fallback
        mock_qualer_api_fetcher.fetch_via_browser.return_value = {
            "Data": [],
            "Total": 0,
        }

        # Execute
        result = clients_read()

        # Verify fallback was used
        assert result["Total"] == 0
        mock_qualer_api_fetcher.fetch_via_browser.assert_called_once()

    @patch("utils.auth.QualerAPIFetcher")
    def test_request_headers_include_browser_fingerprint(
        self, mock_fetcher_class, mock_qualer_api_fetcher, mock_driver
    ):
        """Test that HTTP requests include required browser fingerprinting headers."""
        # Setup
        mock_fetcher_class.return_value = mock_qualer_api_fetcher
        mock_qualer_api_fetcher.driver = mock_driver
        mock_qualer_api_fetcher.extract_csrf_token.return_value = "csrf_token"

        headers_with_fingerprint = {
            "referer": "https://jgiquality.qualer.com/clients",
            "sec-ch-ua": '"Google Chrome";v="120"',
            "user-agent": "Mozilla/5.0",
            "x-requested-with": "XMLHttpRequest",
        }
        mock_qualer_api_fetcher.get_headers.return_value = headers_with_fingerprint

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Data": [], "Total": 0}
        mock_qualer_api_fetcher.session.post.return_value = mock_response

        # Execute
        clients_read()

        # Verify headers were passed correctly
        call_args = mock_qualer_api_fetcher.session.post.call_args
        assert call_args.kwargs["headers"] == headers_with_fingerprint

    @patch("utils.auth.QualerAPIFetcher")
    @patch.dict("os.environ", {"QUALER_PAGE_LOAD_WAIT_TIME": "5"})
    def test_configurable_page_load_wait(
        self, mock_fetcher_class, mock_qualer_api_fetcher, mock_driver
    ):
        """Test that page load wait time is configurable via environment variable."""
        # Setup
        mock_fetcher_class.return_value = mock_qualer_api_fetcher
        mock_qualer_api_fetcher.driver = mock_driver
        mock_qualer_api_fetcher.extract_csrf_token.return_value = "csrf_token"
        mock_qualer_api_fetcher.get_headers.return_value = {}

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Data": [], "Total": 0}
        mock_qualer_api_fetcher.session.post.return_value = mock_response

        with patch(
            "qualer_internal_sdk.endpoints.client_dashboard.clients_read.sleep"
        ) as mock_sleep:
            # Execute
            clients_read()

            # Verify sleep was called with configured value
            mock_sleep.assert_called_with(5.0)


class TestCookieSyncErrors:
    """Test cases for cookie synchronization error handling."""

    @patch("utils.auth.QualerAPIFetcher")
    def test_no_driver_error(self, mock_fetcher_class):
        """Test error handling when driver is not initialized."""
        # Setup
        mock_fetcher = Mock()
        mock_fetcher.__enter__ = Mock(return_value=mock_fetcher)
        mock_fetcher.__exit__ = Mock(return_value=False)
        mock_fetcher.driver = None
        mock_fetcher_class.return_value = mock_fetcher

        # Execute and verify
        with pytest.raises(RuntimeError, match="Failed to initialize Selenium driver"):
            clients_read()

    @patch("utils.auth.QualerAPIFetcher")
    def test_no_session_error(self, mock_fetcher_class, mock_driver):
        """Test error handling when session is not initialized."""
        # Setup
        mock_fetcher = Mock()
        mock_fetcher.__enter__ = Mock(return_value=mock_fetcher)
        mock_fetcher.__exit__ = Mock(return_value=False)
        mock_fetcher.driver = mock_driver
        mock_fetcher.session = None
        mock_fetcher.extract_csrf_token.return_value = "csrf_token"
        mock_fetcher.get_headers.return_value = {}
        mock_fetcher_class.return_value = mock_fetcher

        # Execute and verify
        with pytest.raises(RuntimeError, match="Failed to establish authenticated session"):
            clients_read()


class TestSyncCookiesFromDriver:
    """Test cases for _sync_cookies_from_driver method."""

    def test_basic_cookie_transfer(self):
        """Test that cookies are transferred correctly from Selenium to requests.Session."""
        # Create a fetcher instance without full initialization
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        
        # Setup mock driver with basic cookies
        mock_driver = Mock()
        mock_driver.get_cookies.return_value = [
            {
                "name": "session_id",
                "value": "abc123",
                "domain": ".qualer.com",
                "path": "/",
                "secure": True,
            },
            {
                "name": "user_token",
                "value": "xyz789",
                "domain": ".qualer.com",
                "path": "/api",
                "secure": False,
            },
        ]
        
        # Setup session
        fetcher.driver = mock_driver
        fetcher.session = Mock()
        fetcher.session.cookies = Mock()
        
        # Execute
        fetcher._sync_cookies_from_driver()
        
        # Verify cookies were set
        assert fetcher.session.cookies.set_cookie.call_count == 2

    def test_domain_path_secure_attributes_preserved(self):
        """Test that domain, path, and secure attributes are preserved during transfer."""
        # Create a fetcher instance
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        
        # Setup mock driver with cookie having specific attributes
        mock_driver = Mock()
        test_cookie = {
            "name": "auth_cookie",
            "value": "secure_value_123",
            "domain": ".jgiquality.qualer.com",
            "path": "/clients",
            "secure": True,
        }
        mock_driver.get_cookies.return_value = [test_cookie]
        
        # Setup session with actual cookie jar to verify attributes
        import requests
        fetcher.driver = mock_driver
        fetcher.session = requests.Session()
        
        # Execute
        fetcher._sync_cookies_from_driver()
        
        # Verify cookie was added to session
        cookies = list(fetcher.session.cookies)
        assert len(cookies) == 1
        
        # Verify attributes are preserved
        cookie = cookies[0]
        assert cookie.name == "auth_cookie"
        assert cookie.value == "secure_value_123"
        assert cookie.domain == ".jgiquality.qualer.com"
        assert cookie.path == "/clients"
        assert cookie.secure is True

    def test_suffixed_cookie_names(self):
        """Test that cookies with suffixed names (e.g., __RequestVerificationToken_L3...) work correctly."""
        # Create a fetcher instance
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        
        # Setup mock driver with suffixed cookie name (ASP.NET anti-forgery pattern)
        mock_driver = Mock()
        suffixed_cookies = [
            {
                "name": "__RequestVerificationToken",
                "value": "base_token_value",
                "domain": ".qualer.com",
                "path": "/",
                "secure": True,
            },
            {
                "name": "__RequestVerificationToken_L3NoYXJlZC1zZWN1cmVk0",
                "value": "suffixed_token_value_CfDJ8ABC123",
                "domain": ".qualer.com",
                "path": "/shared-secured",
                "secure": True,
            },
        ]
        mock_driver.get_cookies.return_value = suffixed_cookies
        
        # Setup session
        import requests
        fetcher.driver = mock_driver
        fetcher.session = requests.Session()
        
        # Execute
        fetcher._sync_cookies_from_driver()
        
        # Verify both cookies were added
        cookies = list(fetcher.session.cookies)
        assert len(cookies) == 2
        
        # Verify suffixed cookie is present with correct value
        suffixed_cookie = next(
            (c for c in cookies if c.name.startswith("__RequestVerificationToken_")),
            None
        )
        assert suffixed_cookie is not None
        assert suffixed_cookie.value == "suffixed_token_value_CfDJ8ABC123"
        assert suffixed_cookie.path == "/shared-secured"

    def test_cookies_missing_name_are_skipped(self):
        """Test that cookies without a name are skipped gracefully."""
        # Create a fetcher instance
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        
        # Setup mock driver with malformed cookie (missing name)
        mock_driver = Mock()
        mock_driver.get_cookies.return_value = [
            {
                "value": "orphaned_value",
                "domain": ".qualer.com",
                "path": "/",
            },
            {
                "name": "valid_cookie",
                "value": "valid_value",
                "domain": ".qualer.com",
                "path": "/",
            },
        ]
        
        # Setup session
        import requests
        fetcher.driver = mock_driver
        fetcher.session = requests.Session()
        
        # Execute - should not raise error
        fetcher._sync_cookies_from_driver()
        
        # Verify only valid cookie was added
        cookies = list(fetcher.session.cookies)
        assert len(cookies) == 1
        assert cookies[0].name == "valid_cookie"

    def test_cookies_missing_value_are_skipped(self):
        """Test that cookies without a value are skipped gracefully."""
        # Create a fetcher instance
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        
        # Setup mock driver with malformed cookie (missing value)
        mock_driver = Mock()
        mock_driver.get_cookies.return_value = [
            {
                "name": "empty_cookie",
                "domain": ".qualer.com",
                "path": "/",
            },
            {
                "name": "valid_cookie",
                "value": "valid_value",
                "domain": ".qualer.com",
                "path": "/",
            },
        ]
        
        # Setup session
        import requests
        fetcher.driver = mock_driver
        fetcher.session = requests.Session()
        
        # Execute - should not raise error
        fetcher._sync_cookies_from_driver()
        
        # Verify only valid cookie was added
        cookies = list(fetcher.session.cookies)
        assert len(cookies) == 1
        assert cookies[0].name == "valid_cookie"

    def test_cookies_with_empty_string_name_are_skipped(self):
        """Test that cookies with empty string name are skipped."""
        # Create a fetcher instance
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        
        # Setup mock driver with cookie having empty name
        mock_driver = Mock()
        mock_driver.get_cookies.return_value = [
            {
                "name": "",
                "value": "some_value",
                "domain": ".qualer.com",
                "path": "/",
            },
            {
                "name": "valid_cookie",
                "value": "valid_value",
                "domain": ".qualer.com",
                "path": "/",
            },
        ]
        
        # Setup session
        import requests
        fetcher.driver = mock_driver
        fetcher.session = requests.Session()
        
        # Execute
        fetcher._sync_cookies_from_driver()
        
        # Verify only valid cookie was added
        cookies = list(fetcher.session.cookies)
        assert len(cookies) == 1
        assert cookies[0].name == "valid_cookie"

    def test_default_path_applied_when_missing(self):
        """Test that path defaults to '/' when not provided by driver."""
        # Create a fetcher instance
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        
        # Setup mock driver with cookie missing path attribute
        mock_driver = Mock()
        mock_driver.get_cookies.return_value = [
            {
                "name": "no_path_cookie",
                "value": "value123",
                "domain": ".qualer.com",
                "secure": False,
            }
        ]
        
        # Setup session
        import requests
        fetcher.driver = mock_driver
        fetcher.session = requests.Session()
        
        # Execute
        fetcher._sync_cookies_from_driver()
        
        # Verify cookie was added with default path
        cookies = list(fetcher.session.cookies)
        assert len(cookies) == 1
        assert cookies[0].path == "/"

    def test_default_secure_false_when_missing(self):
        """Test that secure defaults to False when not provided by driver."""
        # Create a fetcher instance
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        
        # Setup mock driver with cookie missing secure attribute
        mock_driver = Mock()
        mock_driver.get_cookies.return_value = [
            {
                "name": "no_secure_cookie",
                "value": "value456",
                "domain": ".qualer.com",
                "path": "/",
            }
        ]
        
        # Setup session
        import requests
        fetcher.driver = mock_driver
        fetcher.session = requests.Session()
        
        # Execute
        fetcher._sync_cookies_from_driver()
        
        # Verify cookie was added with default secure=False
        cookies = list(fetcher.session.cookies)
        assert len(cookies) == 1
        assert cookies[0].secure is False

    def test_multiple_cookies_with_different_domains(self):
        """Test handling of multiple cookies with different domain attributes."""
        # Create a fetcher instance
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        
        # Setup mock driver with cookies from different domains
        mock_driver = Mock()
        mock_driver.get_cookies.return_value = [
            {
                "name": "qualer_cookie",
                "value": "qualer_value",
                "domain": ".qualer.com",
                "path": "/",
                "secure": True,
            },
            {
                "name": "jgi_cookie",
                "value": "jgi_value",
                "domain": ".jgiquality.qualer.com",
                "path": "/",
                "secure": True,
            },
        ]
        
        # Setup session
        import requests
        fetcher.driver = mock_driver
        fetcher.session = requests.Session()
        
        # Execute
        fetcher._sync_cookies_from_driver()
        
        # Verify both cookies were added with correct domains
        cookies = list(fetcher.session.cookies)
        assert len(cookies) == 2
        
        domains = [c.domain for c in cookies]
        assert ".qualer.com" in domains
        assert ".jgiquality.qualer.com" in domains

    def test_assertion_error_when_session_is_none(self):
        """Test that assertion fails when session is None."""
        # Create a fetcher instance
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        
        # Setup with None session
        mock_driver = Mock()
        mock_driver.get_cookies.return_value = []
        fetcher.driver = mock_driver
        fetcher.session = None
        
        # Execute and verify assertion error
        with pytest.raises(AssertionError):
            fetcher._sync_cookies_from_driver()

    def test_assertion_error_when_driver_is_none(self):
        """Test that assertion fails when driver is None."""
        # Create a fetcher instance
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        
        # Setup with None driver
        import requests
        fetcher.driver = None
        fetcher.session = requests.Session()
        
        # Execute and verify assertion error
        with pytest.raises(AssertionError):
            fetcher._sync_cookies_from_driver()
