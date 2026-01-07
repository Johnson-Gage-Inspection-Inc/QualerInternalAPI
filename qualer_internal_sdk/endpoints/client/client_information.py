"""Fetch client information HTML from Qualer and store in database.

Endpoint: GET /Client/ClientInformation
"""

from typing import Optional

from utils.auth import QualerAPIFetcher
from tqdm import tqdm


def fetch_and_store(client_ids: list, api: Optional[QualerAPIFetcher] = None) -> None:
    """
    Fetch and store client information for all clients.

    Fetches the HTML form for each client from the Qualer API and stores
    the raw responses in the datadump table for later parsing.

    Args:
        client_ids: List of client IDs to fetch
        api: Optional QualerAPIFetcher instance. If not provided, creates new context manager.
    """

    def _do_fetch(fetcher):
        for client_id in tqdm(client_ids, desc="Fetching client data", dynamic_ncols=True):
            url = f"https://jgiquality.qualer.com/Client/ClientInformation?clientId={client_id}"
            try:
                fetcher.fetch_and_store(url, "ClientInformation")
            except Exception as e:
                # Skip clients with permission errors or other failures
                print(f"\nWarning: Failed to fetch client {client_id}: {e}")
                continue

    if api:
        _do_fetch(api)
    else:
        with QualerAPIFetcher() as api:
            _do_fetch(api)
