"""Dataclasses for validating Qualer API response structures."""

from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class UncertaintyParameter:
    """Schema for a single uncertainty parameter object."""

    HideParameterAbbreviation: bool
    ParameterAbbreviation: Optional[str]
    ParameterType: int
    ParameterName: Optional[str]
    ParameterId: int
    ValueType: int
    Value: float
    Text: Optional[str]
    DoubleArrayValue: Optional[List[Any]]


@dataclass
class UncertaintyParametersResponse:
    """Schema for UncertaintyParameters API response."""

    Success: bool
    Parameters: List[UncertaintyParameter]
    MuParameters: Optional[List[Any]]

    @classmethod
    def from_dict(cls, data: dict) -> "UncertaintyParametersResponse":
        """Create instance from dictionary, validating structure."""
        try:
            parameters = [UncertaintyParameter(**param) for param in data.get("Parameters", [])]
            return cls(
                Success=data["Success"],
                Parameters=parameters,
                MuParameters=data.get("MuParameters"),
            )
        except (KeyError, TypeError) as e:
            raise ValueError(f"Invalid UncertaintyParametersResponse structure: {e}")
