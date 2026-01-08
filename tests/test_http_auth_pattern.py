"""Tests for HTTP-first authentication pattern with browser fallback."""

import pytest
from unittest.mock import Mock, patch
from qualer_internal_sdk.endpoints.client_dashboard.clients_read import clients_read


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

    @patch("qualer_internal_sdk.endpoints.client_dashboard.clients_read.QualerAPIFetcher")
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

    @patch("qualer_internal_sdk.endpoints.client_dashboard.clients_read.QualerAPIFetcher")
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

    @patch("qualer_internal_sdk.endpoints.client_dashboard.clients_read.QualerAPIFetcher")
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

    @patch("qualer_internal_sdk.endpoints.client_dashboard.clients_read.QualerAPIFetcher")
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

    @patch("qualer_internal_sdk.endpoints.client_dashboard.clients_read.QualerAPIFetcher")
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

    @patch("qualer_internal_sdk.endpoints.client_dashboard.clients_read.QualerAPIFetcher")
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

    @patch("qualer_internal_sdk.endpoints.client_dashboard.clients_read.QualerAPIFetcher")
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

    @patch("qualer_internal_sdk.endpoints.client_dashboard.clients_read.QualerAPIFetcher")
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
