import json
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup


def get_client_information(
    client_id: int,
    cookies: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Fetch client information from Qualer API and parse the HTML response.

    Requires authentication cookies from an active Qualer session.
    See EXAMPLE_COOKIES variable below for the required cookies.

    Args:
        client_id: The client ID to fetch information for
        cookies: Dictionary of authentication cookies. If None, will attempt
                 to use default cookies.

    Returns:
        Dictionary containing the parsed client information

    Raises:
        requests.exceptions.RequestException: If the API request fails
    """
    url = (
        "https://jgiquality.qualer.com/Client/"
        f"ClientInformation?clientId={client_id}"
    )

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

    # Use a session to handle cookies/credentials
    session = requests.Session()
    if cookies:
        session.cookies.update(cookies)

    try:
        response = session.get(url, headers=headers, timeout=10)
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


# Example cookies required for authentication
# These should be obtained from an active Qualer session
EXAMPLE_COOKIES = {
    "_fuid": "YWI1NjEyMmMtMjlmMC00ZWM1LWI3ZTctNzQzZjY2ZGU5NDNk",
    "__utmz": (
        "147229740.1757527976.45.2.utmcsr=excel.officeapps.live.com"
        "|utmccn=(referral)|utmcmd=referral|utmcct=/"
    ),
    "GUID": "acadcd3b-26e1-441a-a0fe-db75e2088e55",
    "Qualer.Employee.Login.SessionId": ("918d9403f0ab4febaa74fa26ead665f7"),
    "__RequestVerificationToken_L3NoYXJlZC1zZWN1cmVk0": (
        "IUVgIlmwo3zgnUwGBQxc7XN2T3fA1aXYJ7AhxdjyeDwd2ndcZCPjmgMVN-"
        "cd9Zqs0z8Y1JzfJ1-lCzGuqxygqF5HztQ1"
    ),
    "__utmc": "147229740",
    "__utma": "147229740.1751280352.1751238350.1767652796.1767734700.120",
    "Qualer.auth": (
        "03633F414765DC8DC7A1A55B28279683600018839981B091B067E67E4A0811C35C"
        "10C7867C44D3FAEC4FFDE023FB5C46DDC1FD06B713C7432FE22A4EE9798C13ABB6D1"
        "CFCCA4C1550802D6B0EAF729151647DAB1D2873B615BBF072B89FE49C602CA3B17264"
        "169C561B3462D85B8C00880BD32BEEA20CD59FAAD8E8CF6694B83ED99AD3D72F71ACD"
        "912DA0B40B55A087DE91116F"
    ),
    "__utmb": "147229740.10.10.1767734700",
    "RT": (
        "z=1&dm=qualer.com&si=a97cc615-8778-4ba6-a180-0759bf590f61"
        "&ss=mk33lix9&sl=49&tt=2k02"
        "&bcn=https%3A%2F%2Fmetrics.qualer.com%2Fapi%2Fmetrics"
    ),
    "ASP.NET_SessionId": "ayaikhxyq5uo3vdwcopvc1vi",
}


if __name__ == "__main__":
    # Example usage with authentication cookies
    client_id = 152226
    try:
        data = get_client_information(client_id, cookies=EXAMPLE_COOKIES)
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Failed to get client information: {e}")
