"""
Example usage of the ServiceMeasurement_Read endpoint.

This demonstrates how to:
1. Authenticate with Qualer
2. Fetch measurement data for a service group
3. Use both the script and SDK approaches
"""

import json
from utils.auth import QualerAPIFetcher
from qualer_internal_sdk.endpoints.service import get_service_measurements


def example_using_sdk():
    """Example using the SDK function."""
    print("=== Using SDK Function ===\n")

    # Service group ID to fetch measurements for
    service_group_id = 14397  # Replace with your service group ID

    with QualerAPIFetcher(headless=True) as fetcher:
        # Fetch measurements using SDK function
        result = get_service_measurements(service_group_id, fetcher)

        # Handle Kendo DataSource response
        if isinstance(result, dict):
            measurements = result.get("Data", [])
            total = result.get("Total", 0)
            print(f"Found {len(measurements)} measurements (Total: {total})")

            # Print first measurement as example
            if measurements:
                print("\nFirst measurement:")
                print(json.dumps(measurements[0], indent=2))
        else:
            print(f"Unexpected response format: {type(result)}")


def example_using_script():
    """Example using the standalone script approach."""
    print("\n=== Using Script Approach ===\n")

    from scripts.getServiceMeasurements import get_service_measurements

    service_group_id = 14397  # Replace with your service group ID

    with QualerAPIFetcher(headless=True) as fetcher:
        # Fetch measurements using script function
        result = get_service_measurements(service_group_id, fetcher=fetcher)

        # Handle response
        if isinstance(result, dict):
            measurements = result.get("Data", [])
            print(f"Found {len(measurements)} measurements")

            # Show measurement fields
            if measurements:
                print("\nAvailable fields in measurements:")
                print(list(measurements[0].keys()))


def example_with_filters():
    """Example using sorting and filtering."""
    print("\n=== Using Filters and Sorting ===\n")

    service_group_id = 14397  # Replace with your service group ID

    with QualerAPIFetcher(headless=True) as fetcher:
        # Fetch with sorting
        result = get_service_measurements(
            service_group_id,
            fetcher,
            sort="Name-asc",  # Sort by Name ascending
            filter_param="",  # Kendo filter syntax (if needed)
        )

        if isinstance(result, dict):
            measurements = result.get("Data", [])
            print(f"Found {len(measurements)} measurements (sorted)")

            # Print names to show sorting
            if measurements:
                print("\nMeasurement names (sorted):")
                for m in measurements[:5]:  # Show first 5
                    print(f"  - {m.get('Name', 'N/A')}")


if __name__ == "__main__":
    # Run examples
    try:
        example_using_sdk()
    except Exception as e:
        print(f"SDK example failed: {e}")

    try:
        example_using_script()
    except Exception as e:
        print(f"Script example failed: {e}")

    try:
        example_with_filters()
    except Exception as e:
        print(f"Filter example failed: {e}")
