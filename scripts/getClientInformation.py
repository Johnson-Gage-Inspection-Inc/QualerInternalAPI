import sys
import json
import os
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm


def get_client_information(
    client_id: int,
    session: Optional[requests.Session] = None,
    cookies: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Fetch client information from Qualer API and parse the HTML response.

    Requires authentication via either a requests.Session with valid cookies
    or a dictionary of authentication cookies.

    Args:
        client_id: The client ID to fetch information for
        session: Optional requests.Session with authentication cookies already set.
                 If provided, this takes precedence over the cookies parameter.
        cookies: Optional dictionary of authentication cookies.
                 Only used if session is not provided.

    Returns:
        Dictionary containing the parsed client information

    Raises:
        requests.exceptions.RequestException: If the API request fails
    """
    url = "https://jgiquality.qualer.com/Client/" f"ClientInformation?clientId={client_id}"

    headers = {
        "accept": "text/html, */*; q=0.01",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache, must-revalidate",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": (
            f"https://jgiquality.qualer.com/client/account?"
            f"clientId={client_id}&startFilter=CompanyInformation"
        ),
        "sec-ch-ua": ('"Google Chrome";v="143", "Chromium";v="143", ' '"Not A(Brand";v="24"'),
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-requested-with": "XMLHttpRequest",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        ),
    }

    # Use provided session or create a new one
    if session is None:
        session = requests.Session()
        if cookies:
            session.cookies.update(cookies)

    try:
        timeout = float(os.getenv("QUALER_REQUEST_TIMEOUT", "30"))
        response = session.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()  # Raise exception for bad status codes

        # Parse HTML response
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract all form input values
        client_data: Dict[str, Any] = {}
        form = soup.find("form", {"id": "ClientInformation"})

        if form:
            # Extract all input fields
            for input_field in form.find_all("input"):
                name = input_field.get("name")
                value = input_field.get("value", "")

                if name and isinstance(name, str):
                    client_data[name] = value

        if not client_data:
            # If no form found, return raw text for debugging
            print("Warning: Could not find ClientInformation form")
            return {"raw_response": response.text[:1000]}

        return client_data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching client information: {e}")
        raise


def get_client_information_with_auth(
    client_id: int,
    username: Optional[str] = None,
    password: Optional[str] = None,
    headless: bool = True,
) -> Dict[str, Any]:
    """
    Fetch client information using QualerAPIFetcher for automatic authentication.

    This function handles the full authentication flow using Selenium and
    extracts cookies for the API request.

    Args:
        client_id: The client ID to fetch information for
        username: Optional Qualer username. If not provided, will prompt or use env var.
        password: Optional Qualer password. If not provided, will prompt or use env var.
        headless: Whether to run Selenium in headless mode (default True)

    Returns:
        Dictionary containing the parsed client information

    Raises:
        RuntimeError: If authentication fails
        requests.exceptions.RequestException: If the API request fails
    """
    from utils.auth import QualerAPIFetcher

    with QualerAPIFetcher(username=username, password=password, headless=headless) as fetcher:
        return get_client_information(client_id, session=fetcher.session)


if __name__ == "__main__":
    from utils.auth import QualerAPIFetcher

    with open("clients.json", "r", encoding="utf-8") as f:
        clients = json.load(f)
    if not clients:
        print("No clients found")
        sys.exit(1)

    data_list = []
    client_ids: list[int] = [c["Id"] for c in clients["Data"] if c.get("Id")]
    with QualerAPIFetcher(headless=False) as fetcher:
        for client_id in tqdm(client_ids, desc="Fetching client information", dynamic_ncols=True):
            try:
                data = get_client_information(client_id, session=fetcher.session)
                data_list.append(data)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    # Skip clients you don't have access to
                    continue
                else:
                    print(f"Failed to get client {client_id}: {e}")
            except Exception as e:
                print(f"Failed to get client {client_id}: {e}")

    # Optionally, store all client data to a JSON file
    with open("client_account_data.json", "w", encoding="utf-8") as outfile:
        json.dump(data_list, outfile, indent=2)

    # Also, flatten and store to CSV
    df = pd.json_normalize(data_list)
    df.to_csv("client_account_data.csv", index=False)
