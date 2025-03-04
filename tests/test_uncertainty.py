# test_uncertainty.py

import pytest
from my_qualer_utils import QualerAPIFetcher
import json


@pytest.fixture
def qualer_api():
    # Provide any needed parameters or environment variables
    with QualerAPIFetcher() as api:
        yield api


def test_uncertainty_parameters(qualer_api):
    url = "https://jgiquality.qualer.com/work/Uncertainties/UncertaintyParameters?measurementId=89052138&uncertaintyBudgetId=8001"
    response = qualer_api.fetch(url)

    with open("tests/testdata/UncertaintyParamters.json") as f:
        assert response.json() == json.load(f)

    assert response.status_code == 200
