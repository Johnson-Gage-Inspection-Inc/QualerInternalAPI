"""
Extract service level parameters from Qualer API.

This script fetches service level parameter data for specified service groups
and saves the results to JSON and CSV files.

Usage:
    python scripts/getServiceLevelParameters.py
"""

import json
import pandas as pd
from utils.auth import QualerAPIFetcher
from qualer_internal_sdk.endpoints.service.service_level_parameters import (
    get_service_level_parameters,
)


def main():
    """Main execution function."""
    # Example service group ID (replace with your actual ID)
    service_group_id = 14397

    print(f"Fetching service level parameters for service group {service_group_id}...")

    with QualerAPIFetcher() as fetcher:
        # Fetch parameters for single service group
        parameters = get_service_level_parameters(service_group_id, fetcher)

        print(f"Found {len(parameters)} service level parameters")

        # Save to JSON
        json_output = "service_level_parameters.json"
        with open(json_output, "w") as f:
            json.dump([vars(param) for param in parameters], f, indent=2)
        print(f"Saved to {json_output}")

        # Convert to DataFrame and save as CSV
        df = pd.json_normalize([vars(param) for param in parameters])
        csv_output = "service_level_parameters.csv"
        df.to_csv(csv_output, index=False)
        print(f"Saved to {csv_output}")

        # Example: Fetch for multiple service groups
        # Uncomment and modify as needed
        """
        service_group_ids = [14397, 14398, 14399]
        print(f"\nFetching parameters for {len(service_group_ids)} service groups...")

        all_parameters = get_all_parameters_for_groups(service_group_ids, fetcher)

        # Save bulk results
        bulk_output = "service_level_parameters_by_group.json"
        with open(bulk_output, "w") as f:
            json.dump(
                {
                    str(group_id): [vars(param) for param in params]
                    for group_id, params in all_parameters.items()
                },
                f,
                indent=2
            )
        print(f"Saved bulk results to {bulk_output}")
        """


if __name__ == "__main__":
    main()
