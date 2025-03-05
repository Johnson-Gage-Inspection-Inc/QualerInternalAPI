import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import urlparse, parse_qs
import json

# Connect to your Postgres DB (adjust connection string as needed)
engine = create_engine("postgresql://postgres:postgres@192.168.1.177:5432/qualer")

# Read only the URL and response_body from datadump for UncertaintyModal where not yet parsed
df = pd.read_sql(
    "SELECT url, response_body FROM datadump WHERE service = 'UncertaintyModal' AND parsed = FALSE LIMIT 10", engine
)


# Function to extract query parameters from a URL
def extract_params(url):
    parsed = urlparse(url)
    return {key: values[0] for key, values in parse_qs(parsed.query).items()}


# Convert the extracted parameters into a DataFrame
params_df = pd.DataFrame(df['url'].apply(extract_params).tolist())


# Function to parse the JSON response body
def parse_response(response):
    try:
        response_dict = json.loads(response)
        if not response_dict.pop("Success", None):
            raise ValueError("Response indicated failure")
        # Get the uncertainty budget ID where Selected is True
        uncertainties = pd.DataFrame(response_dict.pop("Uncertainties", {}))
        if 'Selected' in uncertainties.columns and uncertainties['Selected'].dtype == bool:
            selected_ids = uncertainties.loc[uncertainties['Selected'], 'Id'].tolist()
            response_dict['UncertaintyBudgetId'] = selected_ids[0] if selected_ids else ''
        else:
            response_dict['UncertaintyBudgetId'] = ''

        MeasurementParameters = pd.DataFrame(response_dict.pop("MeasurementParameters", {}))
        MeasurementParameters.to_sql("measurement_parameters", engine, if_exists="append", index=False)
        response_dict['ParameterIds'] = MeasurementParameters['ParameterId'].tolist()
        return response_dict
    except Exception:
        return {}


# Parse the JSON in the response_body and convert into a DataFrame
response_df = pd.DataFrame(df['response_body'].apply(parse_response).tolist())

# Combine the query parameters and the parsed response data
combined_df = pd.concat([params_df, response_df], axis=1)

# Save the resulting DataFrame to a new PostgreSQL table
combined_df.to_sql("uncertainty_modal_clean", engine, if_exists="replace", index=False)

# Update the datadump table to mark these rows as parsed
with engine.begin() as conn:
    conn.execute(
        "UPDATE datadump SET parsed = TRUE WHERE service = 'UncertaintyModal' AND parsed = FALSE"
    )
