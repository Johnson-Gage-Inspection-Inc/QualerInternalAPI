"""
Service Level Parameter endpoint for Qualer Internal API.

This module provides access to the ServiceLevelParameter_Read endpoint,
which returns parameter configurations for service measurements within a service group.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from utils.auth import QualerAPIFetcher


@dataclass
class ServiceLevelParameter:
    """
    Represents a service level parameter from the Qualer API.

    Service level parameters define acceptable ranges and measurement settings
    for service measurements (e.g., AsFoundAcceptableMin, AsLeftPoints, etc.).
    """

    # Required fields
    id: int
    service_group_id: int
    service_measurement_id: int
    service_parameter_id: int
    service_measurement: str
    default_value: str
    parameter_type: str
    display_order: int
    service_level_parameter_views: List[Any]

    # Optional fields (can be null in API response)
    service_parameter_level_id: Optional[int]
    service_level_parameter_id: Optional[int]
    service_parameter_value: Optional[str]
    service_level_name: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceLevelParameter":
        """
        Create a ServiceLevelParameter instance from a dictionary.

        Args:
            data: Dictionary from API response

        Returns:
            ServiceLevelParameter instance

        Raises:
            KeyError: If a required field is missing from the response
        """
        return cls(
            id=data["Id"],
            service_group_id=data["ServiceGroupId"],
            service_measurement_id=data["ServiceMeasurementId"],
            service_parameter_id=data["ServiceParameterId"],
            service_measurement=data["ServiceMeasurement"],
            default_value=data["DefaultValue"],
            parameter_type=data["ParameterType"],
            display_order=data["DisplayOrder"],
            service_level_parameter_views=data["ServiceLevelParameterViews"],
            service_parameter_level_id=data.get("ServiceParameterLevelId"),
            service_level_parameter_id=data.get("ServiceLevelParameterId"),
            service_parameter_value=data.get("ServiceParameterValue"),
            service_level_name=data.get("ServiceLevelName"),
        )


def get_service_level_parameters(
    service_group_id: int,
    fetcher: QualerAPIFetcher,
    sort: str = "DisplayOrder-asc~ServiceMeasurement-asc",
    group: str = "",
    filter_param: str = "",
) -> List[ServiceLevelParameter]:
    """
    Fetch service level parameters for a specific service group.

    Args:
        service_group_id: The ID of the service group to fetch parameters for
        fetcher: Authenticated QualerAPIFetcher instance
        sort: Sort order (default: "DisplayOrder-asc~ServiceMeasurement-asc")
        group: Grouping parameter (default: empty string)
        filter_param: Filter parameter (default: empty string)

    Returns:
        List of ServiceLevelParameter objects

    Raises:
        requests.HTTPError: If the API request fails
        KeyError: If expected fields are missing from the response
    """
    url = "https://jgiquality.qualer.com/ServiceParameter/ServiceLevelParameter_Read"
    params = {"ServiceGroupId": service_group_id}

    # Build form data
    data = {
        "sort": sort,
        "page": 1,
        "pageSize": 25,
        "group": group,
        "filter": filter_param,
    }

    # Make POST request (fetcher.post() handles CSRF token automatically)
    response = fetcher.post(url, data=data, params=params)
    response.raise_for_status()

    # Parse response
    json_response = response.json()

    # Check for API errors
    if json_response.get("Errors"):
        response.status_code = 400
        response.reason = f"API Error: {json_response['Errors']}"
        response.raise_for_status()

    # Extract and convert data
    parameters_data = json_response.get("Data", [])
    return [ServiceLevelParameter.from_dict(param) for param in parameters_data]


def get_all_parameters_for_groups(
    service_group_ids: List[int], fetcher: QualerAPIFetcher
) -> Dict[int, List[ServiceLevelParameter]]:
    """
    Fetch service level parameters for multiple service groups in bulk.

    Args:
        service_group_ids: List of service group IDs to fetch parameters for
        fetcher: Authenticated QualerAPIFetcher instance

    Returns:
        Dictionary mapping service group ID to list of ServiceLevelParameter objects

    Note:
        Skips groups that return 403 Forbidden (insufficient permissions)
    """
    results = {}

    for group_id in service_group_ids:
        try:
            parameters = get_service_level_parameters(group_id, fetcher)
            results[group_id] = parameters
        except Exception as e:
            if "403" in str(e):
                print(f"Skipping service group {group_id} (403 Forbidden)")
                continue
            raise

    return results
