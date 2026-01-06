import json
from typing import Any, Dict

import requests


def get_client_information(client_id: int) -> Dict[str, Any] | str:
    """
    Fetch client information from Qualer API.

    Args:
        client_id: The client ID to fetch information for

    Returns:
        Dictionary containing the client information response
    """
    url = (
        "https://jgiquality.qualer.com/Client/"
        f"ClientInformation?clientId={client_id}"
    )

    headers = {
        "accept": "text/html, */*; q=0.01",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache, must-revalidate",
        "clientrequesttime": "2026-01-06T15:32:12",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "sec-ch-ua": (
            '"Google Chrome";v="143", "Chromium";v="143", ' '"Not A(Brand";v="24"'
        ),
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-requested-with": "XMLHttpRequest",
    }

    # Use a session to handle cookies/credentials
    session = requests.Session()

    try:
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise exception for bad status codes
        return response.json() if response.text else response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching client information: {e}")
        raise


if __name__ == "__main__":
    # Example usage
    client_id = 152226
    try:
        data = get_client_information(client_id)
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Failed to get client information: {e}")
