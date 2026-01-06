"""
Template for creating new Qualer internal API extraction scripts.

Workflow:
1. Find data on https://jgiquality.qualer.com
2. Open Chrome DevTools (F12) → Network tab
3. Perform the action to fetch data
4. Find the Fetch/XHR request in Network tab
5. Right-click → Copy as → Copy as fetch/cURL/PowerShell
6. Extract: URL, headers, request body, response structure
7. Copy this template and fill in the blanks below
"""

import json
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm


def get_entity_information(
    entity_id: int,
    session: Optional[requests.Session] = None,
    cookies: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Fetch entity information from Qualer's internal API.

    TODO: Update docstring with actual entity description.

    Args:
        entity_id: The entity ID to fetch information for
        session: Optional requests.Session with authentication cookies already set.
        cookies: Optional dictionary of authentication cookies.

    Returns:
        Dictionary containing the parsed entity information

    Raises:
        requests.exceptions.RequestException: If the API request fails
    """
    # TODO: Replace with actual endpoint from Chrome Network inspector
    url = (
        "https://jgiquality.qualer.com/Entity/"
        f"EntityInformation?entityId={entity_id}"
    )

    headers = {
        "accept": "text/html, */*; q=0.01",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache, must-revalidate",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": (
            f"https://jgiquality.qualer.com/entity/account?" f"entityId={entity_id}"
        ),
        "sec-ch-ua": (
            '"Google Chrome";v="143", "Chromium";v="143", ' '"Not A(Brand";v="24"'
        ),
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

    # TODO: Add request body if POST/PUT request
    # request_body = {"field": "value"}

    # Use provided session or create a new one
    if session is None:
        session = requests.Session()
        if cookies:
            session.cookies.update(cookies)

    try:
        # TODO: Change to session.post() if needed, add json=request_body
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse HTML response
        soup = BeautifulSoup(response.text, "html.parser")

        # TODO: Update form ID to match actual form from HTML response
        entity_data: Dict[str, Any] = {}
        form = soup.find("form", {"id": "EntityInformation"})

        if form:
            # Extract all input fields
            for input_field in form.find_all("input"):
                name = input_field.get("name")
                value = input_field.get("value", "")

                if name and isinstance(name, str):
                    entity_data[name] = value

        if not entity_data:
            print("Warning: Could not find EntityInformation form")
            return {"raw_response": response.text[:1000]}

        return entity_data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching entity information: {e}")
        raise


if __name__ == "__main__":
    from my_qualer_utils import QualerAPIFetcher

    # TODO: Update with actual data source
    with open("entities.json", "r", encoding="utf-8") as f:
        entities = json.load(f)

    if not entities:
        print("No entities found")
        exit(1)

    data_list: List[Dict[str, Any]] = []
    # TODO: Update to match actual data structure
    entity_ids: list[int] = [e["Id"] for e in entities["Data"] if e.get("Id")]

    with QualerAPIFetcher(headless=False) as fetcher:
        for entity_id in tqdm(
            entity_ids,
            desc="Fetching entity information",
            dynamic_ncols=True,
        ):
            try:
                data = get_entity_information(entity_id, session=fetcher.session)
                data_list.append(data)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    # Skip entities you don't have access to
                    continue
                else:
                    print(f"Failed to get entity {entity_id}: {e}")
            except Exception as e:
                print(f"Failed to get entity {entity_id}: {e}")

    # Store results
    with open("entity_data.json", "w", encoding="utf-8") as outfile:
        json.dump(data_list, outfile, indent=2)

    # Also flatten and store to CSV
    df = pd.json_normalize(data_list)
    df.to_csv("entity_data.csv", index=False)
    print(f"Saved {len(data_list)} entities to entity_data.json and .csv")
