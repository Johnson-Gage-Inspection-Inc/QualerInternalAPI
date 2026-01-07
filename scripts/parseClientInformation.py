"""
Parse client information from stored HTML responses.

This script reads the raw HTML responses from the datadump table,
extracts form fields using BeautifulSoup, and outputs to JSON/CSV.
"""

import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

from utils.html_parser import extract_form_fields

load_dotenv()

DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise EnvironmentError("DB_URL environment variable is not set")

engine = create_engine(DB_URL)


def main():
    """Parse stored ClientInformation responses and export to CSV/JSON."""
    # Read only the response_body from datadump for ClientInformation
    df = pd.read_sql(
        "SELECT response_body FROM datadump WHERE service = :service",
        engine,
        params={"service": "ClientInformation"},
    )

    if df.empty:
        print("No ClientInformation responses found in datadump")
        return

    # Extract form fields from each HTML response
    parsed_data = []
    for html in df["response_body"]:
        fields = extract_form_fields(html, "ClientInformation")
        if fields:
            parsed_data.append(fields)

    if not parsed_data:
        print("No form fields could be extracted")
        return

    # Convert to DataFrame and export
    parsed_df = pd.DataFrame(parsed_data)

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # JSON
    parsed_df.to_json("data/client_information.json", orient="records", indent=2)

    # CSV
    parsed_df.to_csv("data/client_information.csv", index=False)

    print(f"Parsed {len(parsed_data)} client records")
    print("Saved to data/client_information.json and data/client_information.csv")


if __name__ == "__main__":
    main()
