# test_uncertainty.py

import pytest
import os
from utils.auth import QualerAPIFetcher
from persistence.storage import PostgresRawStorage
import json

from qualer_internal_sdk.schemas import UncertaintyParametersResponse


@pytest.fixture
def qualer_api():
    """Fixture for tests requiring actual Qualer authentication (skipped in CI)."""
    # Skip if no credentials available (CI environment)
    username = os.getenv("QUALER_USERNAME")
    password = os.getenv("QUALER_PASSWORD")

    if not username or not password:
        pytest.skip("Qualer credentials not available (set QUALER_USERNAME and QUALER_PASSWORD)")

    with QualerAPIFetcher(username=username, password=password) as api:
        yield api


def test_run_sql(db_url):
    """Test run_sql using testcontainer database (no Qualer auth needed)."""
    # Create storage adapter with test database
    storage = PostgresRawStorage(db_url)

    # Create test table and data
    storage.run_sql(
        """
        CREATE TABLE IF NOT EXISTS company_certifications (
            certification_id INTEGER PRIMARY KEY
        )
    """
    )
    storage.run_sql("INSERT INTO company_certifications (certification_id) VALUES (284)")

    # Test the query
    result = storage.run_sql("SELECT certification_id FROM company_certifications;")
    assert result[0][0] == 284

    # Cleanup
    storage.close()


@pytest.mark.skip(reason="Live API data changes frequently - requires Qualer credentials")
def test_uncertainty_parameters(qualer_api):
    """Test fetching uncertainty parameters from live API."""
    url = "https://jgiquality.qualer.com/work/Uncertainties/UncertaintyParameters?measurementId=89052138&uncertaintyBudgetId=8001"
    response = qualer_api.fetch(url)

    assert response.status_code == 200
    data = response.json()
    # Validate that response can be cast to the schema
    result = UncertaintyParametersResponse.from_dict(data)
    assert result.Success is not None
    assert isinstance(result.Parameters, list)


def test_store(qualer_api):
    count = qualer_api.run_sql("SELECT COUNT(*) FROM datadump;")[0][0]
    url = "https://jgiquality.qualer.com/work/Uncertainties/UncertaintyParameters?measurementId=89052138&uncertaintyBudgetId=8001"
    service = "UncertaintyParameters"
    method = "GET"
    response = qualer_api.fetch(url)
    qualer_api.store(url, service, method, response)
    assert qualer_api.run_sql("SELECT COUNT(*) FROM datadump;")[0][0] == 1 + count

    latest_response_body = qualer_api.run_sql("SELECT response_body FROM datadump;")[-1][0]
    stored_data = json.loads(latest_response_body)
    # Validate that stored data can be cast to the schema
    result = UncertaintyParametersResponse.from_dict(stored_data)
    assert result.Success is not None
