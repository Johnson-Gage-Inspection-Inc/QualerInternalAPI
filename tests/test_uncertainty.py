# test_uncertainty.py

import pytest
from utils.auth import QualerAPIFetcher
import json

from qualer_internal_sdk.schemas import UncertaintyParametersResponse


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
    # Validate that response can be cast to the schema
    result = UncertaintyParametersResponse.from_dict(data)
    assert result.Success is not None
    assert isinstance(result.Parameters, list)


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
    # Validate that stored data can be cast to the schema
    result = UncertaintyParametersResponse.from_dict(stored_data)
    assert result.Success is not None
