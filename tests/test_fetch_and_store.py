"""Tests for the refactored fetch_and_store method."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from utils.auth import QualerAPIFetcher


class TestFetchAndStore:
    """Tests for fetch_and_store method."""

    @patch("utils.auth.QualerAPIFetcher.store")
    @patch("utils.auth.QualerAPIFetcher.fetch")
    def test_fetch_and_store_html_response(self, mock_fetch, mock_store):
        """Test fetch_and_store delegates to fetch() and store()."""
        # Setup mocks
        mock_response = Mock()
        mock_fetch.return_value = mock_response

        # Mock storage adapter
        mock_storage = MagicMock()

        # Create fetcher and set up required attributes
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        fetcher.storage = mock_storage

        # Call method
        fetcher.fetch_and_store("https://example.com", "TestService", method="GET")

        # Verify fetch was called with the URL
        mock_fetch.assert_called_once_with("https://example.com")

        # Verify store was called with the response
        mock_store.assert_called_once_with(
            "https://example.com", "TestService", "GET", mock_response
        )

    @patch("utils.auth.QualerAPIFetcher._build_requests_session")
    @patch("utils.auth.QualerAPIFetcher._login")
    @patch("utils.auth.QualerAPIFetcher._init_driver")
    def test_fetch_and_store_json_response(self, mock_init, mock_login, mock_session):
        """Test fetch_and_store with JSON response."""
        # Setup mocks
        mock_driver = Mock()
        mock_driver.page_source = '<html><body><pre>{"key": "value"}</pre></body></html>'

        mock_session_obj = Mock()
        mock_response = Mock()
        mock_response.headers.get.return_value = "application/json"
        mock_response.request.headers = {"User-Agent": "test"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_session_obj.get.return_value = mock_response

        # Mock storage adapter
        mock_storage = MagicMock()

        # Create fetcher and set up required attributes
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        fetcher.driver = mock_driver
        fetcher.session = mock_session_obj
        fetcher.storage = mock_storage

        # Call method
        fetcher.fetch_and_store("https://example.com", "TestService")

        # Verify storage adapter was called
        assert mock_storage.store_response.called

    @patch("utils.auth.QualerAPIFetcher._build_requests_session")
    @patch("utils.auth.QualerAPIFetcher._login")
    @patch("utils.auth.QualerAPIFetcher._init_driver")
    def test_fetch_and_store_json_with_charset(self, mock_init, mock_login, mock_session):
        """Test fetch_and_store handles JSON content-type with charset parameter."""
        # Setup mocks
        mock_driver = Mock()
        mock_driver.page_source = '<html><body><pre>{"data": "test"}</pre></body></html>'

        mock_session_obj = Mock()
        mock_response = Mock()
        mock_response.headers.get.return_value = "application/json; charset=utf-8"
        mock_response.request.headers = {"User-Agent": "test"}
        mock_response.headers = {"Content-Type": "application/json; charset=utf-8"}
        mock_session_obj.get.return_value = mock_response

        # Mock storage adapter
        mock_storage = MagicMock()

        # Create fetcher and set up required attributes
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        fetcher.driver = mock_driver
        fetcher.session = mock_session_obj
        fetcher.storage = mock_storage

        # Call method
        fetcher.fetch_and_store("https://example.com", "TestService")

        # Verify storage adapter was called
        assert mock_storage.store_response.called

    @patch("utils.auth.QualerAPIFetcher.fetch")
    def test_fetch_and_store_no_session_raises_error(self, mock_fetch):
        """Test that RuntimeError is raised if storage is not configured."""
        # Mock fetch to succeed
        mock_fetch.return_value = Mock()

        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        fetcher.driver = Mock()
        fetcher.session = None
        fetcher.storage = None

        with pytest.raises(RuntimeError, match="No storage configured"):
            fetcher.fetch_and_store("https://example.com", "TestService")

    @patch("utils.auth.QualerAPIFetcher.fetch")
    def test_fetch_and_store_no_driver_raises_error(self, mock_fetch):
        """Test that RuntimeError is raised if fetch fails (which checks driver)."""
        # Mock fetch to raise RuntimeError
        mock_fetch.side_effect = RuntimeError("No valid session")

        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        fetcher.driver = None
        fetcher.session = Mock()
        fetcher.storage = Mock()

        with pytest.raises(RuntimeError, match="No valid session"):
            fetcher.fetch_and_store("https://example.com", "TestService")
