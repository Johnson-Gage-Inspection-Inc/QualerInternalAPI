"""
Fetch client information HTML from Qualer and store in database.

This script uses the client.client_information endpoint to fetch and store
client HTML forms for later parsing.
"""

from qualer_internal_sdk.endpoints.client import client_information


def main():
    """Fetch and store client information for all clients."""
    client_information.main()


if __name__ == "__main__":
    main()
