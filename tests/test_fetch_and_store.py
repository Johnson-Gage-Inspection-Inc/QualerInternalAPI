"""Tests for the refactored fetch_and_store method."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from utils.auth import QualerAPIFetcher


class TestFetchAndStore:
    """Tests for fetch_and_store method."""

    @patch('utils.auth.QualerAPIFetcher._build_requests_session')
    @patch('utils.auth.QualerAPIFetcher._login')
    @patch('utils.auth.QualerAPIFetcher._init_driver')
    @patch('utils.auth.create_engine')
    def test_fetch_and_store_html_response(self, mock_engine, mock_init, mock_login, mock_session):
        """Test fetch_and_store with HTML response."""
        # Setup mocks
        mock_driver = Mock()
        mock_driver.page_source = "<html><body>Test HTML</body></html>"
        
        mock_session_obj = Mock()
        mock_response = Mock()
        mock_response.headers.get.return_value = "text/html"
        mock_response.request.headers = {"User-Agent": "test"}
        mock_response.headers = {"Content-Type": "text/html"}
        mock_session_obj.get.return_value = mock_response
        
        mock_conn = Mock()
        mock_engine_obj = Mock()
        mock_engine_obj.begin.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_engine_obj.begin.return_value.__exit__ = Mock(return_value=False)
        mock_engine.return_value = mock_engine_obj

        # Create fetcher and set up required attributes
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        fetcher.driver = mock_driver
        fetcher.session = mock_session_obj
        fetcher.engine = mock_engine_obj

        # Call method
        fetcher.fetch_and_store("https://example.com", "TestService")

        # Verify session.get was called
        mock_session_obj.get.assert_called_once_with("https://example.com")

        # Verify driver.get was called
        mock_driver.get.assert_called_once_with("https://example.com")

        # Verify database insert was called
        mock_conn.execute.assert_called_once()

    @patch('utils.auth.QualerAPIFetcher._build_requests_session')
    @patch('utils.auth.QualerAPIFetcher._login')
    @patch('utils.auth.QualerAPIFetcher._init_driver')
    @patch('utils.auth.create_engine')
    def test_fetch_and_store_json_response(self, mock_engine, mock_init, mock_login, mock_session):
        """Test fetch_and_store with JSON response."""
        # Setup mocks
        mock_driver = Mock()
        mock_driver.page_source = "<html><body><pre>{\"key\": \"value\"}</pre></body></html>"
        
        mock_session_obj = Mock()
        mock_response = Mock()
        mock_response.headers.get.return_value = "application/json"
        mock_response.request.headers = {"User-Agent": "test"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_session_obj.get.return_value = mock_response
        
        mock_conn = Mock()
        mock_engine_obj = Mock()
        mock_engine_obj.begin.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_engine_obj.begin.return_value.__exit__ = Mock(return_value=False)
        mock_engine.return_value = mock_engine_obj

        # Create fetcher and set up required attributes
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        fetcher.driver = mock_driver
        fetcher.session = mock_session_obj
        fetcher.engine = mock_engine_obj

        # Call method
        fetcher.fetch_and_store("https://example.com", "TestService")

        # Verify the call was made
        assert mock_conn.execute.called

    @patch('utils.auth.QualerAPIFetcher._build_requests_session')
    @patch('utils.auth.QualerAPIFetcher._login')
    @patch('utils.auth.QualerAPIFetcher._init_driver')
    @patch('utils.auth.create_engine')
    def test_fetch_and_store_json_with_charset(self, mock_engine, mock_init, mock_login, mock_session):
        """Test fetch_and_store handles JSON content-type with charset parameter."""
        # Setup mocks
        mock_driver = Mock()
        mock_driver.page_source = "<html><body><pre>{\"data\": \"test\"}</pre></body></html>"
        
        mock_session_obj = Mock()
        mock_response = Mock()
        mock_response.headers.get.return_value = "application/json; charset=utf-8"
        mock_response.request.headers = {"User-Agent": "test"}
        mock_response.headers = {"Content-Type": "application/json; charset=utf-8"}
        mock_session_obj.get.return_value = mock_response
        
        mock_conn = Mock()
        mock_engine_obj = Mock()
        mock_engine_obj.begin.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_engine_obj.begin.return_value.__exit__ = Mock(return_value=False)
        mock_engine.return_value = mock_engine_obj

        # Create fetcher and set up required attributes
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        fetcher.driver = mock_driver
        fetcher.session = mock_session_obj
        fetcher.engine = mock_engine_obj

        # Call method
        fetcher.fetch_and_store("https://example.com", "TestService")

        # Verify database call was made
        assert mock_conn.execute.called

    def test_fetch_and_store_no_session_raises_error(self):
        """Test that RuntimeError is raised if session is not initialized."""
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        fetcher.driver = Mock()
        fetcher.session = None
        fetcher.engine = Mock()

        with pytest.raises(RuntimeError, match="Driver or session not initialized"):
            fetcher.fetch_and_store("https://example.com", "TestService")

    def test_fetch_and_store_no_driver_raises_error(self):
        """Test that RuntimeError is raised if driver is not initialized."""
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        fetcher.driver = None
        fetcher.session = Mock()
        fetcher.engine = Mock()

        with pytest.raises(RuntimeError, match="Driver or session not initialized"):
            fetcher.fetch_and_store("https://example.com", "TestService")
