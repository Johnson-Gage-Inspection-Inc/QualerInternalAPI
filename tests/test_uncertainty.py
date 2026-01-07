# test_uncertainty.py

import pytest
from utils.auth import QualerAPIFetcher
import json


@pytest.fixture
def qualer_api():
    # Provide any needed parameters or environment variables
    with QualerAPIFetcher() as api:
        yield api


@pytest.mark.skip(reason="Live API data changes frequently")
def test_uncertainty_parameters(qualer_api):
    url = "https://jgiquality.qualer.com/work/Uncertainties/UncertaintyParameters?measurementId=89052138&uncertaintyBudgetId=8001"
    response = qualer_api.fetch(url)

    assert response.status_code == 200
    data = response.json()
    # Validate expected schema
    assert isinstance(data, dict)
    assert "Success" in data
    assert isinstance(data["Success"], bool)
    assert "Parameters" in data
    assert isinstance(data["Parameters"], list)
    assert "MuParameters" in data


def test_run_sql(qualer_api):
    sql_query = "SELECT certification_id FROM company_certifications;"
    result = qualer_api.run_sql(sql_query)
    assert result[0][0] == 284


@pytest.mark.skip(reason="Live API data changes frequently")
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
    # Validate stored data has expected schema
    assert isinstance(stored_data, dict)
    assert "Success" in stored_data
    assert isinstance(stored_data["Success"], bool)
    assert "Parameters" in stored_data
    assert isinstance(stored_data["Parameters"], list)
