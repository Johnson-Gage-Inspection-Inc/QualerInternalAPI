"""Tests for service endpoint modules."""

import pytest
from unittest.mock import Mock
from qualer_internal_sdk.endpoints.service.service_groups import ServiceGroupsEndpoint


@pytest.fixture
def mock_session():
    """Create a mock session."""
    return Mock()


@pytest.fixture
def mock_driver():
    """Create a mock Selenium driver."""
    return Mock()


@pytest.fixture
def service_endpoint(mock_session, mock_driver):
    """Create a ServiceGroupsEndpoint with mocks."""
    return ServiceGroupsEndpoint(mock_session, mock_driver)


class TestServiceGroupsEndpoint:
    """Test cases for ServiceGroupsEndpoint."""

    def test_get_service_groups_json_response(self, service_endpoint, mock_session):
        """Test fetching service groups with JSON response."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"id": 1, "name": "Group 1"}]}
        mock_response.headers = {"content-type": "application/json"}
        mock_session.get.return_value = mock_response

        # Execute
        result = service_endpoint.get_service_groups(123)

        # Verify
        assert result == {"data": [{"id": 1, "name": "Group 1"}]}
        mock_session.get.assert_called_once()

    def test_get_service_groups_no_session(self):
        """Test that error is raised if no session."""
        endpoint = ServiceGroupsEndpoint(None)
        with pytest.raises(RuntimeError, match="Session not available"):
            endpoint.get_service_groups(123)

    def test_fetch_for_service_order_items(self, service_endpoint, mock_session):
        """Test fetching for multiple items."""
        # Setup mock responses
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        mock_response.headers = {"content-type": "application/json"}
        mock_session.get.return_value = mock_response

        # Execute
        results = service_endpoint.fetch_for_service_order_items([1, 2, 3])

        # Verify
        assert len(results) == 3
        assert mock_session.get.call_count == 3

    def test_fetch_for_service_order_items_with_error(self, service_endpoint, mock_session):
        """Test that errors are handled gracefully."""
        # Setup mock to raise exception
        mock_session.get.side_effect = Exception("Network error")

        # Execute
        results = service_endpoint.fetch_for_service_order_items([1, 2])

        # Verify - errors are stored, not raised
        assert len(results) == 2
        assert "error" in results[1]
        assert "error" in results[2]

    def test_get_service_groups_calls_correct_url(self, service_endpoint, mock_session):
        """Test that correct URL is called."""
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.headers = {"content-type": "application/json"}
        mock_session.get.return_value = mock_response

        service_endpoint.get_service_groups(999)

        # Verify URL contains the service_order_item_id
        call_args = mock_session.get.call_args
        assert "999" in call_args[0][0]
        assert "GetServiceGroupsForExistingLevels" in call_args[0][0]
