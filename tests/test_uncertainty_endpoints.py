"""Tests for uncertainty endpoint modules."""

import pytest
from unittest.mock import Mock
from qualer_internal_sdk.endpoints.uncertainty.uncertainty_parameters import (
    UncertaintyParametersEndpoint,
)
from qualer_internal_sdk.endpoints.uncertainty.uncertainty_modal import (
    UncertaintyModalEndpoint,
)


@pytest.fixture
def mock_session():
    """Create a mock session."""
    return Mock()


@pytest.fixture
def mock_driver():
    """Create a mock Selenium driver."""
    return Mock()


@pytest.fixture
def parameters_endpoint(mock_session, mock_driver):
    """Create an UncertaintyParametersEndpoint with mocks."""
    return UncertaintyParametersEndpoint(mock_session, mock_driver)


@pytest.fixture
def modal_endpoint(mock_session, mock_driver):
    """Create an UncertaintyModalEndpoint with mocks."""
    return UncertaintyModalEndpoint(mock_session, mock_driver)


class TestUncertaintyParametersEndpoint:
    """Test cases for UncertaintyParametersEndpoint."""

    def test_get_parameters_json_response(self, parameters_endpoint, mock_session):
        """Test fetching uncertainty parameters with JSON response."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {"parameters": [{"name": "param1", "value": 1.0}]}
        mock_response.headers = {"content-type": "application/json"}
        mock_session.get.return_value = mock_response

        # Execute
        result = parameters_endpoint.get_parameters(123, 456)

        # Verify
        assert result == {"parameters": [{"name": "param1", "value": 1.0}]}
        mock_session.get.assert_called_once()

    def test_get_parameters_no_session(self):
        """Test that error is raised if no session."""
        endpoint = UncertaintyParametersEndpoint(None)
        with pytest.raises(RuntimeError, match="Session not available"):
            endpoint.get_parameters(123, 456)

    def test_fetch_for_measurements(self, parameters_endpoint, mock_session):
        """Test fetching for multiple measurement/budget combinations."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        mock_response.headers = {"content-type": "application/json"}
        mock_session.get.return_value = mock_response

        # Execute - 2 measurements x 2 budgets = 4 requests
        results = parameters_endpoint.fetch_for_measurements([1, 2], [10, 20])

        # Verify
        assert len(results) == 4
        assert mock_session.get.call_count == 4

    def test_fetch_for_measurements_with_errors(self, parameters_endpoint, mock_session):
        """Test that errors are handled gracefully in batch fetch."""
        # Setup mock to raise exception
        mock_session.get.side_effect = Exception("Network error")

        # Execute
        results = parameters_endpoint.fetch_for_measurements([1, 2], [10, 20])

        # Verify - all failed gracefully
        assert len(results) == 4
        for result in results.values():
            assert "error" in result

    def test_get_parameters_calls_correct_url(self, parameters_endpoint, mock_session):
        """Test that correct URL is called."""
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.headers = {"content-type": "application/json"}
        mock_session.get.return_value = mock_response

        parameters_endpoint.get_parameters(999, 888)

        # Verify URL contains both IDs
        call_args = mock_session.get.call_args
        url = call_args[0][0]
        assert "999" in url
        assert "888" in url
        assert "UncertaintyParameters" in url


class TestUncertaintyModalEndpoint:
    """Test cases for UncertaintyModalEndpoint."""

    def test_get_modal_json_response(self, modal_endpoint, mock_session):
        """Test fetching uncertainty modal with JSON response."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {"modal_data": {"id": 1}}
        mock_response.headers = {"content-type": "application/json"}
        mock_session.get.return_value = mock_response

        # Execute
        result = modal_endpoint.get_modal(123, 456)

        # Verify
        assert result == {"modal_data": {"id": 1}}
        mock_session.get.assert_called_once()

    def test_get_modal_no_session(self):
        """Test that error is raised if no session."""
        endpoint = UncertaintyModalEndpoint(None)
        with pytest.raises(RuntimeError, match="Session not available"):
            endpoint.get_modal(123, 456)

    def test_fetch_for_measurements(self, modal_endpoint, mock_session):
        """Test fetching for multiple measurement/batch combinations."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        mock_response.headers = {"content-type": "application/json"}
        mock_session.get.return_value = mock_response

        # Execute - 3 measurement/batch combinations
        measurement_batches = [(1, 100), (2, 200), (3, 300)]
        results = modal_endpoint.fetch_for_measurements(measurement_batches)

        # Verify
        assert len(results) == 3
        assert mock_session.get.call_count == 3

    def test_get_modal_calls_correct_url(self, modal_endpoint, mock_session):
        """Test that correct URL is called."""
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.headers = {"content-type": "application/json"}
        mock_session.get.return_value = mock_response

        modal_endpoint.get_modal(999, 888)

        # Verify URL contains both IDs
        call_args = mock_session.get.call_args
        url = call_args[0][0]
        assert "999" in url
        assert "888" in url
        assert "UncertaintyModal" in url
