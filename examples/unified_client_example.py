"""
Example: Using the unified QualerClient interface.

Demonstrates the new Phase 4 API that provides a clean, unified way to
access all Qualer endpoints.
"""

import json
from qualer_internal_sdk import QualerClient


def example_basic_usage():
    """Example 1: Basic usage - fetch all clients."""
    print("Example 1: Basic Usage")
    print("-" * 50)

    with QualerClient() as client:
        # Fetch all clients using the unified interface
        print("Fetching all clients...")
        clients_response = client.client_dashboard.clients_read()
        # API returns "Data" (capital D) in the response
        clients = clients_response.get("Data", [])
        print(f"✓ Found {len(clients)} clients")

        if clients:
            print(f"  First client: {clients[0].get('Name', 'Unknown')}")


def example_fetch_and_store():
    """Example 2: Fetch client information and store in database."""
    print("\nExample 2: Fetch and Store Client Information")
    print("-" * 50)

    with QualerClient() as client:
        # Fetch all clients
        print("Fetching clients...")
        clients_response = client.client_dashboard.clients_read()
        clients = clients_response.get("Data", [])
        client_ids = [c["Id"] for c in clients]
        print(f"✓ Found {len(client_ids)} clients")

        # Fetch and store information for each client
        if client_ids:
            print(f"Fetching information for {len(client_ids)} clients...")
            client.client.fetch_and_store(client_ids)
            print("✓ Information stored in database")


def example_full_workflow():
    """Example 3: Complete workflow with persistence."""
    print("\nExample 3: Full Workflow with Data Persistence")
    print("-" * 50)

    with QualerClient() as client:
        # Step 1: Fetch clients
        print("Step 1: Fetching clients from Qualer...")
        clients_response = client.client_dashboard.clients_read()
        clients = clients_response.get("Data", [])
        print(f"  ✓ Found {len(clients)} clients")

        # Step 2: Save to data/clients.json for other scripts
        print("Step 2: Saving client list to data/clients.json...")
        with open("data/clients.json", "w") as f:
            json.dump({"clients": clients}, f, indent=2)
        print("  ✓ Client list saved")

        # Step 3: Fetch and store detailed information
        client_ids = [c["Id"] for c in clients]
        if client_ids:
            print(f"Step 3: Fetching detailed info for {len(client_ids)} clients...")
            client.client.fetch_and_store(client_ids)
            print("  ✓ Information stored in database")

        print("\nWorkflow complete!")


def example_with_custom_options():
    """Example 4: Using custom options for debugging."""
    print("\nExample 4: Custom Configuration")
    print("-" * 50)

    # See the browser during execution
    print("Opening browser (headless=False) for 10 seconds after login...")
    with QualerClient(headless=False, login_wait_time=10.0) as client:
        print("Fetching clients...")
        clients_response = client.client_dashboard.clients_read()
        clients = clients_response.get("Data", [])
        print(f"✓ Found {len(clients)} clients")


if __name__ == "__main__":
    print("=" * 50)
    print("QualerClient Unified Interface Examples")
    print("=" * 50)

    try:
        # Run examples
        # Uncomment the examples you want to run:

        example_basic_usage()
        # example_fetch_and_store()
        # example_full_workflow()
        # example_with_custom_options()

    except Exception as e:
        print(f"✗ Error: {e}")
