"""
Extract service measurement data from Qualer's ServiceMeasurement_Read endpoint.

Endpoint: POST /ServiceMeasurement/ServiceMeasurement_Read
Discovered: 2026-01-15 via Chrome DevTools on ServiceMeasurement page
Returns: JSON array of measurements for a service group
"""

import sys
import json
import os
from typing import Any, Dict, List, Optional

import requests
import pandas as pd
from tqdm import tqdm


def get_service_measurements(
    service_group_id: int,
    fetcher: Optional["QualerAPIFetcher"] = None,
    sort: str = "",
    group: str = "",
    filter_param: str = "",
) -> Dict[str, Any]:
    """
    Fetch service measurements for a given service group.

    Args:
        service_group_id: The service group ID to fetch measurements for
        fetcher: QualerAPIFetcher instance with authenticated session
        sort: Optional sort parameter for Kendo grid
        group: Optional group parameter for Kendo grid
        filter_param: Optional filter parameter for Kendo grid

    Returns:
        Dictionary containing the service measurement data

    Raises:
        requests.exceptions.RequestException: If the API request fails
    """
    url = "https://jgiquality.qualer.com/ServiceMeasurement/ServiceMeasurement_Read"

    if fetcher is None:
        raise ValueError("fetcher parameter is required")

    # Prepare form data (CSRF token will be added automatically)
    form_data = {
        "sort": sort,
        "group": group,
        "filter": filter_param,
        "serviceGroupId": service_group_id,
    }

    try:
        timeout = float(os.getenv("QUALER_REQUEST_TIMEOUT", "30"))
        # Use fetcher.post() which handles CSRF tokens and headers automatically
        response = fetcher.post(
            url,
            data=form_data,
            referer=(
                f"https://jgiquality.qualer.com/ServiceMeasurement/ServiceMeasurement?"
                f"ServiceGroupId={service_group_id}"
            ),
            timeout=timeout,
        )

        # Parse JSON response
        data = response.json()
        return data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching service measurements: {e}")
        raise


if __name__ == "__main__":
    from utils.auth import QualerAPIFetcher

    # Load service groups from previous extraction
    service_groups_file = "service_groups.json"
    if not os.path.exists(service_groups_file):
        print(f"Error: {service_groups_file} not found")
        print("Run getServiceGroups.py first to get service group IDs")
        sys.exit(1)

    with open(service_groups_file, "r", encoding="utf-8") as f:
        service_groups_data = json.load(f)

    # Extract service group IDs
    service_group_ids: List[int] = []
    if isinstance(service_groups_data, dict) and "Data" in service_groups_data:
        service_group_ids = [sg["Id"] for sg in service_groups_data["Data"] if sg.get("Id")]
    elif isinstance(service_groups_data, list):
        service_group_ids = [sg["Id"] for sg in service_groups_data if sg.get("Id")]

    if not service_group_ids:
        print("No service groups found")
        sys.exit(1)

    print(f"Found {len(service_group_ids)} service groups")

    # Collect all measurements
    all_measurements: List[Dict[str, Any]] = []
    measurements_by_group: Dict[int, List[Dict[str, Any]]] = {}

    with QualerAPIFetcher(headless=True) as fetcher:
        for sg_id in tqdm(
            service_group_ids,
            desc="Fetching service measurements",
            dynamic_ncols=True,
        ):
            try:
                result = get_service_measurements(sg_id, fetcher=fetcher)

                # Handle Kendo DataSource response format
                if isinstance(result, dict):
                    measurements = result.get("Data", [])
                elif isinstance(result, list):
                    measurements = result
                else:
                    print(f"Unexpected response format for service group {sg_id}")
                    continue

                # Add service group ID to each measurement for tracking
                for measurement in measurements:
                    measurement["ServiceGroupId"] = sg_id
                    all_measurements.append(measurement)

                measurements_by_group[sg_id] = measurements

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    # Skip service groups you don't have access to
                    continue
                else:
                    print(f"Failed to get measurements for service group {sg_id}: {e}")
            except Exception as e:
                print(f"Failed to get measurements for service group {sg_id}: {e}")

    print(
        f"\nFetched {len(all_measurements)} total measurements across {len(measurements_by_group)} service groups"
    )

    # Store all measurements in one file
    with open("service_measurements.json", "w", encoding="utf-8") as outfile:
        json.dump(all_measurements, outfile, indent=2)

    # Store grouped measurements
    with open("service_measurements_by_group.json", "w", encoding="utf-8") as outfile:
        json.dump(measurements_by_group, outfile, indent=2)

    # Flatten and store to CSV
    if all_measurements:
        df = pd.json_normalize(all_measurements)
        df.to_csv("service_measurements.csv", index=False)
        print(
            "Saved to service_measurements.json, service_measurements_by_group.json, and service_measurements.csv"
        )
    else:
        print("No measurements extracted")
