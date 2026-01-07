"""Response type definitions for ClientDashboard API endpoints."""

from typing import TypedDict, List, Any, Dict


class ClientsCountViewResponse(TypedDict):
    """Response structure for ClientsCountView endpoint."""

    Success: bool
    view: "ClientCountsView"


class ClientCountsView(TypedDict):
    """Client counts grouped by filter type."""

    AllClients: int
    Prospects: int  # Matches FilterType.Prospects (plural)
    Delinquent: int
    Inactive: int
    Unapproved: int
    Hidden: int
    OfflineFulfillment: int
    AssetsDue: int
    AssetsPastDue: int
    AssetsPastDuePeriod: int


class ClientsReadResponse(TypedDict):
    """Response structure for Clients_Read endpoint."""

    Data: List[Dict[str, Any]]  # Client records with various fields
    Total: int
    AggregateResults: Any  # Can be None or aggregate data
    Errors: Any  # Can be None or error information
