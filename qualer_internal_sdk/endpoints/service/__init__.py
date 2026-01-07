"""Service API endpoints.

This package serves as the public interface for service-related API
endpoints. Endpoint implementations may live in submodules and will be
re-exported here via ``__all__`` when they are considered stable.
"""

from .service_groups import ServiceGroupsEndpoint

__all__ = [
    "ServiceGroupsEndpoint",
]
