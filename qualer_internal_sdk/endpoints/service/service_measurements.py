"""
Service Measurements endpoint module.

Provides access to the ServiceMeasurement_Read endpoint which returns
measurement data for service groups.
"""

from typing import Any, Dict, List
import os

from dataclasses import dataclass
import requests

from utils.auth import QualerAPIFetcher


@dataclass
class ServiceMeasurement:
    # Example: {'Id': 18095, 'MeasurementName': 'Inside Diameter', 'MeasurementQuantity': 'Length', 'TechniqueName': 'Plain Rings & Inside Cylindrical Diameter', 'BackgroundColor': '#ffffff', 'PointsVaryByServiceLevel': False, 'NumberOfPoints': 1, 'ReadingsVaryByServiceLevel': False, 'NumberOfReadings': 6, 'DisplayOrder': 1, 'Fields': ['Class'], 'IsAsFound': True, 'IsAsLeft': True, 'RepeatMeasurementAndCalculateHysteresis': False, 'DisplayMean': True, 'DisplayMax': False, 'DisplayMin': False, 'DisplayMeasurementError': False, 'DisplayTar': False, 'DisplayTol': False, 'RequireAdjustment': False, 'DisplaySd': True, 'DisplayCv': True, 'DisplayRange': True, 'DisplayDelta': False, 'DisplayMu': True, 'MuDetails': False, 'DisplayTur': False, 'DisplayCmc': False, 'MeanInSpec': False, 'CvInSpec': False, 'MaxInSpec': True, 'MinInSpec': True, 'AcceptableErrorVariesByServiceLevel': False, 'AcceptableTarVariesByServiceLevel': False, 'AdjustmentThresholdVariesByServiceLevel': False, 'OotSignificanceByServiceLevel': False, 'AcceptableCvVariesByServiceLevel': False, 'SdInSpec': False, 'RangeInSpec': True, 'DeltaInSpec': False, 'DisplayAmbiguousPassFail': False, 'AcceptableTurVariesByServiceLevel': False, 'EnvironmentMask': 3, 'Environments': [1, 2]}
    id: int
    measurement_name: str
    measurement_quantity: str
    technique_name: str
    background_color: str
    points_vary_by_service_level: bool
    number_of_points: int
    readings_vary_by_service_level: bool
    number_of_readings: int
    display_order: int
    fields: List[str]
    is_as_found: bool
    is_as_left: bool
    repeat_measurement_and_calculate_hysteresis: bool
    display_mean: bool
    display_max: bool
    display_min: bool
    display_measurement_error: bool
    display_tar: bool
    display_tol: bool
    require_adjustment: bool
    display_sd: bool
    display_cv: bool
    display_range: bool
    display_delta: bool
    display_mu: bool
    mu_details: bool
    display_tur: bool
    display_cmc: bool
    mean_in_spec: bool
    cv_in_spec: bool
    max_in_spec: bool
    min_in_spec: bool
    acceptable_error_varies_by_service_level: bool
    acceptable_tar_varies_by_service_level: bool
    adjustment_threshold_varies_by_service_level: bool
    oot_significance_by_service_level: bool
    acceptable_cv_varies_by_service_level: bool
    sd_in_spec: bool
    range_in_spec: bool
    delta_in_spec: bool
    display_ambiguous_pass_fail: bool
    acceptable_tur_varies_by_service_level: bool
    environment_mask: int
    environments: List[int]

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ServiceMeasurement":
        return ServiceMeasurement(
            id=data["Id"],
            measurement_name=data["MeasurementName"],
            measurement_quantity=data["MeasurementQuantity"],
            technique_name=data["TechniqueName"],
            background_color=data["BackgroundColor"],
            points_vary_by_service_level=data["PointsVaryByServiceLevel"],
            number_of_points=data["NumberOfPoints"],
            readings_vary_by_service_level=data["ReadingsVaryByServiceLevel"],
            number_of_readings=data["NumberOfReadings"],
            display_order=data["DisplayOrder"],
            fields=data.get("Fields", []),
            is_as_found=data["IsAsFound"],
            is_as_left=data["IsAsLeft"],
            repeat_measurement_and_calculate_hysteresis=data[
                "RepeatMeasurementAndCalculateHysteresis"
            ],
            display_mean=data["DisplayMean"],
            display_max=data["DisplayMax"],
            display_min=data["DisplayMin"],
            display_measurement_error=data["DisplayMeasurementError"],
            display_tar=data["DisplayTar"],
            display_tol=data["DisplayTol"],
            require_adjustment=data["RequireAdjustment"],
            display_sd=data["DisplaySd"],
            display_cv=data["DisplayCv"],
            display_range=data["DisplayRange"],
            display_delta=data["DisplayDelta"],
            display_mu=data["DisplayMu"],
            mu_details=data["MuDetails"],
            display_tur=data["DisplayTur"],
            display_cmc=data["DisplayCmc"],
            mean_in_spec=data["MeanInSpec"],
            cv_in_spec=data["CvInSpec"],
            max_in_spec=data["MaxInSpec"],
            min_in_spec=data["MinInSpec"],
            acceptable_error_varies_by_service_level=data["AcceptableErrorVariesByServiceLevel"],
            acceptable_tar_varies_by_service_level=data["AcceptableTarVariesByServiceLevel"],
            adjustment_threshold_varies_by_service_level=data[
                "AdjustmentThresholdVariesByServiceLevel"
            ],
            oot_significance_by_service_level=data["OotSignificanceByServiceLevel"],
            acceptable_cv_varies_by_service_level=data["AcceptableCvVariesByServiceLevel"],
            sd_in_spec=data["SdInSpec"],
            range_in_spec=data["RangeInSpec"],
            delta_in_spec=data["DeltaInSpec"],
            display_ambiguous_pass_fail=data["DisplayAmbiguousPassFail"],
            acceptable_tur_varies_by_service_level=data["AcceptableTurVariesByServiceLevel"],
            environment_mask=data["EnvironmentMask"],
            environments=data.get("Environments", []),
        )


def get_service_measurements(
    service_group_id: int,
    fetcher: QualerAPIFetcher,
    sort: str = "",
    group: str = "",
    filter_param: str = "",
) -> List[ServiceMeasurement]:
    """
    Fetch service measurements for a given service group.

    This endpoint returns measurement data in Kendo DataSource format,
    which is parsed into ServiceMeasurement objects.

    Args:
        service_group_id: The service group ID to fetch measurements for
        fetcher: QualerAPIFetcher instance with authenticated session
        sort: Optional sort parameter for Kendo grid (e.g., "MeasurementName-asc")
        group: Optional group parameter for Kendo grid
        filter_param: Optional filter parameter for Kendo grid (Kendo filter syntax)

    Returns:
        List of ServiceMeasurement objects

    Raises:
        requests.exceptions.RequestException: If the API request fails
        requests.exceptions.HTTPError: If the API returns errors
    """
    url = "https://jgiquality.qualer.com/ServiceMeasurement/ServiceMeasurement_Read"

    # Prepare form data (CSRF token handled automatically by fetcher.post())
    form_data = {
        "sort": sort,
        "group": group,
        "filter": filter_param,
        "serviceGroupId": service_group_id,
    }

    timeout = float(os.getenv("QUALER_REQUEST_TIMEOUT", "30"))
    response = fetcher.post(
        url,
        data=form_data,
        referer=(
            f"https://jgiquality.qualer.com/ServiceMeasurement/ServiceMeasurement?"
            f"ServiceGroupId={service_group_id}"
        ),
        timeout=timeout,
    )

    response_dict = response.json()
    errors = response_dict.get("Errors")
    if errors:
        raise requests.exceptions.HTTPError(
            f"API returned errors: {errors}",
            response=response,
        )

    # For potential future use
    _ = response_dict.get("Total", 0)  # Total count of measurements
    _ = response_dict.get("AggregateResults")  # Aggregate results if any
    data: list = response_dict.get("Data", [])  # List of measurement objects
    return [ServiceMeasurement.from_dict(d) for d in data]


def get_all_measurements_for_groups(
    service_group_ids: List[int],
    fetcher: QualerAPIFetcher,
) -> Dict[int, List[ServiceMeasurement]]:
    """
    Fetch measurements for multiple service groups.

    Args:
        service_group_ids: List of service group IDs
        fetcher: QualerAPIFetcher instance with authenticated session

    Returns:
        Dictionary mapping service group ID to list of ServiceMeasurement objects:
        {
            service_group_id: [measurement1, measurement2, ...],
            ...
        }
    """
    results: Dict[int, List[ServiceMeasurement]] = {}

    for sg_id in service_group_ids:
        try:
            measurements = get_service_measurements(sg_id, fetcher)
            results[sg_id] = measurements

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                # Skip forbidden groups (no access)
                results[sg_id] = []
            else:
                raise

    return results
