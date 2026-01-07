"""Shared types for ClientDashboard endpoints."""

from enum import Enum


class FilterType(str, Enum):
    """Enumeration of filter types for Clients_Read endpoint."""

    AllClients = "AllClients"
    Prospects = "Prospects"
    Delinquent = "Delinquent"
    Inactive = "Inactive"
    Unapproved = "Unapproved"
    Hidden = "Hidden"
    # Managed assets:
    AssetsDue = "AssetsDue"
    AssetsPastDue = "AssetsPastDue"


class SortField(str, Enum):
    """Fields available for sorting clients."""

    ClientCompanyName = "ClientCompanyName"
    ClientAccountNumber = "ClientAccountNumber"
    ContactName = "ContactName"
    CreatedDate = "CreatedDate"
    AssetCount = "AssetCount"
    OrdersCount = "OrdersCount"


class SortOrder(str, Enum):
    """Sort direction."""

    Ascending = "asc"
    Descending = "desc"
