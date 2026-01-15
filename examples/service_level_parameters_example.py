"""
Example usage of the ServiceLevelParameter_Read endpoint.

Demonstrates how to:
1. Fetch parameters for a single service group
2. Fetch parameters for multiple service groups
3. Access parameter data via typed dataclass
"""

from utils.auth import QualerAPIFetcher
from qualer_internal_sdk.endpoints.service.service_level_parameters import (
    get_service_level_parameters,
    get_all_parameters_for_groups,
)


def example_single_group():
    """Fetch parameters for a single service group."""
    print("Example 1: Fetch parameters for a single service group\n")

    with QualerAPIFetcher() as fetcher:
        # Fetch parameters for service group 14397
        parameters = get_service_level_parameters(14397, fetcher)

        print(f"Found {len(parameters)} service level parameters")

        # Access typed parameter data
        for param in parameters[:3]:  # Show first 3
            print(f"\nParameter ID: {param.id}")
            print(f"  Service Measurement: {param.service_measurement}")
            print(f"  Type: {param.parameter_type}")
            print(f"  Default Value: {param.default_value}")
            print(f"  Display Order: {param.display_order}")


def example_multiple_groups():
    """Fetch parameters for multiple service groups."""
    print("\n\nExample 2: Fetch parameters for multiple service groups\n")

    service_group_ids = [14397, 14398, 14399]

    with QualerAPIFetcher() as fetcher:
        # Fetch parameters for all groups
        all_parameters = get_all_parameters_for_groups(service_group_ids, fetcher)

        # Display summary
        for group_id, parameters in all_parameters.items():
            print(f"Service Group {group_id}: {len(parameters)} parameters")


def example_filter_by_type():
    """Filter parameters by type."""
    print("\n\nExample 3: Filter parameters by type\n")

    with QualerAPIFetcher() as fetcher:
        parameters = get_service_level_parameters(14397, fetcher)

        # Group by parameter type
        by_type = {}
        for param in parameters:
            param_type = param.parameter_type
            if param_type not in by_type:
                by_type[param_type] = []
            by_type[param_type].append(param)

        # Display counts
        print("Parameters by type:")
        for param_type, params in by_type.items():
            print(f"  {param_type}: {len(params)}")


if __name__ == "__main__":
    example_single_group()
    example_multiple_groups()
    example_filter_by_type()
