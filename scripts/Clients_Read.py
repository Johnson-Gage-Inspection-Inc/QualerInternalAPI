"""
Fetch client list from Qualer and save to data/clients.json.

This script uses the client_dashboard.clients_read endpoint to fetch the
complete list of clients and save the response as JSON.
"""

import json

from qualer_internal_sdk.endpoints.client_dashboard import clients_read


def main():
    """Fetch clients and save to data/clients.json."""
    print("Fetching clients from Qualer...")

    clients_data = clients_read()

    # Save to file
    with open("data/clients.json", "w", encoding="utf-8") as f:
        json.dump(clients_data, f, indent=2)

    # Print summary
    if isinstance(clients_data, dict):
        total = clients_data.get("total", len(clients_data.get("data", [])))
        print(f"✓ Saved {total} clients to data/clients.json")
    else:
        print(f"✓ Saved {len(clients_data)} clients to data/clients.json")


if __name__ == "__main__":
    main()
