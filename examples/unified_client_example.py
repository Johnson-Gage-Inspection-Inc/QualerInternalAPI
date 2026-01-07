"""
Example: Using the unified QualerClient interface.

Demonstrates the Phase 4-5 unified API that provides a clean way to access
all Qualer endpoints: clients, services, and uncertainty parameters.
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


def example_service_endpoints():
    """Example 3: Fetch service groups using unified interface."""
    print("\nExample 3: Service Groups")
    print("-" * 50)

    with QualerClient() as client:
        # Example: Fetch service groups for a specific service order item
        print("Fetching service groups for service order item 123...")
        try:
            service_groups = client.service.get_service_groups(service_order_item_id=123)
            print(f"✓ Found service groups: {service_groups}")
        except Exception as e:
            print(f"  Note: {e} (This requires valid service order item IDs)")


def example_uncertainty_endpoints():
    """Example 4: Fetch uncertainty data using unified interface."""
    print("\nExample 4: Uncertainty Parameters and Modals")
    print("-" * 50)

    with QualerClient() as client:
        # Example: Fetch uncertainty parameters
        print("Fetching uncertainty parameters...")
        try:
            params = client.uncertainty.get_parameters(
                measurement_id=12345, uncertainty_budget_id=67890
            )
            print(f"✓ Uncertainty parameters: {params}")
        except Exception as e:
            print(f"  Note: {e} (This requires valid measurement/budget IDs)")

        # Example: Fetch uncertainty modal
        print("Fetching uncertainty modal...")
        try:
            modal = client.uncertainty.get_modal(measurement_id=12345, batch_id=999)
            print(f"✓ Uncertainty modal: {modal}")
        except Exception as e:
            print(f"  Note: {e} (This requires valid measurement/batch IDs)")


def example_full_workflow():
    """Example 5: Complete workflow with all endpoint types."""
    print("\nExample 5: Full Workflow with All Endpoints")
    print("-" * 50)

    with QualerClient() as client:
        # Step 1: Fetch clients
        print("Step 1: Fetching clients from Qualer...")
        clients_response = client.client_dashboard.clients_read()
        clients = clients_response.get("Data", [])
        print(f"  ✓ Found {len(clients)} clients")

        # Step 2: Save to data/clients.json
        print("Step 2: Saving client list to data/clients.json...")
        with open("data/clients.json", "w") as f:
            json.dump(clients_response, f, indent=2)
        print("  ✓ Client list saved")

        # Step 3: Fetch and store detailed information
        client_ids = [c["Id"] for c in clients]
        if client_ids:
            print(f"Step 3: Fetching client info for {len(client_ids)} clients...")
            client.client.fetch_and_store(client_ids)
            print("  ✓ Information stored in database")

        # Step 4: Query service groups (example with mock IDs)
        print("Step 4: Fetch service groups...")
        print(
            "  (Skipped in example - requires valid service order item IDs)"
        )

        # Step 5: Query uncertainty data (example with mock IDs)
        print("Step 5: Fetch uncertainty data...")
        print(
            "  (Skipped in example - requires valid measurement/budget IDs)"
        )

        print("\nWorkflow complete!")


def example_with_custom_options():
    """Example 6: Using custom options for debugging."""
    print("\nExample 6: Custom Configuration")
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
        # example_service_endpoints()
        # example_uncertainty_endpoints()
        # example_full_workflow()
        # example_with_custom_options()

    except Exception as e:
        print(f"✗ Error: {e}")
