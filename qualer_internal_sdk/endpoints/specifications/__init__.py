"""Specifications-related endpoints for Qualer Internal API."""

from .standards import (
    Standard,
    StandardsPage,
    get_standards_page,
    get_all_standards,
)

__all__ = [
    "Standard",
    "StandardsPage",
    "get_standards_page",
    "get_all_standards",
]
