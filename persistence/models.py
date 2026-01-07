"""SQLAlchemy ORM models for Qualer API data persistence.

This module provides declarative ORM models for the persistence layer,
enabling developers to query API responses with full SQLAlchemy features
(relationships, lazy loading, query builder, etc.).

Models are designed to match the raw staging tables and support
incremental parsing and enrichment workflows.
"""

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base

# Create base class for all ORM models
Base = declarative_base()


class APIResponse(Base):
    """ORM model for raw API responses in datadump table.

    This model represents a single API call and its response, stored in the
    datadump table. It supports JSON filtering via JSONB operators and
    provides a convenient Python interface for querying and processing
    API responses.

    Attributes:
        id: Unique identifier (serial primary key)
        url: API endpoint URL
        service: Service/endpoint name for organization
        method: HTTP method (GET, POST, etc.)
        request_header: JSON headers sent with request
        response_body: Raw response text/JSON
        response_header: JSON headers from response
        parsed: Whether response has been parsed/processed
        created_at: Timestamp of record creation

    Unique Constraint:
        (url, service, method) - prevents duplicate API calls

    Example:
        >>> from sqlalchemy import create_engine
        >>> from sqlalchemy.orm import Session
        >>> from persistence.models import Base, APIResponse
        >>>
        >>> engine = create_engine("postgresql://localhost/qualer")
        >>> Base.metadata.create_all(engine)
        >>>
        >>> with Session(engine) as session:
        ...     # Query responses for a specific service
        ...     responses = session.query(APIResponse).filter(
        ...         APIResponse.service == "client_information"
        ...     ).all()
        ...
        ...     # Update parse status
        ...     for response in responses:
        ...         if response.response_body:
        ...             response.parsed = True
        ...     session.commit()
    """

    __tablename__ = "datadump"

    id = Column(Integer, primary_key=True)
    """Unique identifier for this API response record."""

    url = Column(String, nullable=False)
    """API endpoint URL that was called."""

    service = Column(String, nullable=False)
    """Service/endpoint name for logical grouping."""

    method = Column(String, nullable=False)
    """HTTP method (GET, POST, PUT, DELETE, etc.)."""

    request_header = Column(JSONB)
    """Request headers as JSONB for flexible querying."""

    response_body = Column(Text)
    """Raw response body (text, JSON, or HTML)."""

    response_header = Column(JSONB)
    """Response headers as JSONB for metadata extraction."""

    parsed = Column(Boolean, default=False)
    """Whether this response has been parsed/processed."""

    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    """Timestamp of record creation."""

    __table_args__ = (UniqueConstraint("url", "service", "method", name="uq_api_response"),)

    def __repr__(self) -> str:
        """Return detailed string representation of APIResponse."""
        return (
            f"APIResponse("
            f"id={self.id}, "
            f"service='{self.service}', "
            f"method={self.method}, "
            f"parsed={self.parsed}, "
            f"created_at={self.created_at})"
        )

    def to_dict(self) -> dict:
        """Convert APIResponse to dictionary.

        Returns:
            Dictionary with all fields, suitable for JSON serialization.
            JSONB columns remain as dicts (not serialized to strings).

        Example:
            >>> response = APIResponse(...)
            >>> data = response.to_dict()
            >>> print(data['request_header'])  # dict, not JSON string
        """
        return {
            "id": self.id,
            "url": self.url,
            "service": self.service,
            "method": self.method,
            "request_header": self.request_header,
            "response_body": self.response_body,
            "response_header": self.response_header,
            "parsed": self.parsed,
            "created_at": (self.created_at.isoformat() if self.created_at is not None else None),
        }


__all__ = ["Base", "APIResponse"]
