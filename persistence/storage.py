"""Storage adapters for API responses - supports PostgreSQL, CSV, and future ORM."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import json
import os
import csv
from datetime import datetime
from sqlalchemy import create_engine, text


class StorageAdapter(ABC):
    """Abstract interface for storing API responses."""

    @abstractmethod
    def store_response(
        self,
        url: str,
        service: str,
        method: str,
        request_headers: Dict[str, Any],
        response_body: str,
        response_headers: Dict[str, Any],
    ) -> None:
        """Store a raw API response."""
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Clean up resources."""
        pass


class PostgresRawStorage(StorageAdapter):
    """
    Stores raw API responses in PostgreSQL datadump table.

    This is the "raw staging" layer - responses are stored as-is for later parsing.
    Schema:
        - url, service, method (composite key)
        - request_header, response_header (JSONB for efficient querying)
        - response_body (TEXT)
        - parsed (BOOLEAN) - flag for downstream processing
    """

    def __init__(self, db_url: str):
        """
        Initialize PostgreSQL storage.

        Args:
            db_url: PostgreSQL connection string (e.g., postgresql://user:pass@host/db)
        """
        self.engine = create_engine(db_url)

    def store_response(
        self,
        url: str,
        service: str,
        method: str,
        request_headers: Dict[str, Any],
        response_body: str,
        response_headers: Dict[str, Any],
    ) -> None:
        """Store response in datadump table with JSONB for headers."""
        if not self.engine:
            raise RuntimeError("Storage engine not initialized")

        try:
            with self.engine.begin() as conn:
                conn.execute(
                    text(
                        """
                        INSERT INTO datadump (
                            url, service, method,
                            request_header, response_body, response_header
                        )
                        VALUES (
                            :url, :service, :method,
                            CAST(:req_headers AS jsonb), :res_body, CAST(:res_headers AS jsonb)
                        )
                        """
                    ),
                    {
                        "url": url,
                        "service": service,
                        "method": method,
                        "req_headers": json.dumps(request_headers) if request_headers else None,
                        "res_body": response_body,
                        "res_headers": json.dumps(response_headers) if response_headers else None,
                    },
                )
        except Exception:
            # Silently ignore duplicate inserts or other errors
            # This is acceptable for staging/raw layer
            pass

    def run_sql(self, sql_query: str, params: Optional[Dict] = None):
        """Execute arbitrary SQL query (for backwards compatibility)."""
        if not self.engine:
            raise RuntimeError("Storage engine not initialized")

        with self.engine.begin() as conn:
            result = conn.execute(text(sql_query), params or {})

            # Only fetch results for queries that return rows (SELECT, RETURNING, etc.)
            if result.returns_rows:
                return result.fetchall()
            return None

    def close(self) -> None:
        """Dispose of SQLAlchemy engine."""
        self.engine.dispose()


class CSVStorage(StorageAdapter):
    """
    Stores API responses as CSV files (for ad-hoc analysis).

    Creates one CSV file per service with columns:
        timestamp, url, method, response_body, request_headers, response_headers

    Useful for quick data exploration without database overhead.

    Note: Not thread-safe. Multiple processes/threads writing to the same CSV file
    may cause duplicate headers or corrupted data. Use PostgresRawStorage for
    concurrent access or implement file locking if concurrent access is required.
    """

    def __init__(self, output_dir: str = "data/responses"):
        """
        Initialize CSV storage.

        Args:
            output_dir: Directory to store CSV files (created if doesn't exist)
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def store_response(
        self,
        url: str,
        service: str,
        method: str,
        request_headers: Dict[str, Any],
        response_body: str,
        response_headers: Dict[str, Any],
    ) -> None:
        """Append response to service-specific CSV file."""
        csv_path = os.path.join(self.output_dir, f"{service}.csv")

        # Check if file exists to determine if we need headers
        file_exists = os.path.exists(csv_path)

        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)

            # Write header if new file
            if not file_exists:
                writer.writerow(
                    [
                        "timestamp",
                        "url",
                        "method",
                        "response_body",
                        "request_headers",
                        "response_headers",
                    ]
                )

            # Write data row
            writer.writerow(
                [
                    datetime.now().isoformat(),
                    url,
                    method,
                    response_body,
                    json.dumps(request_headers),
                    json.dumps(response_headers),
                ]
            )

    def close(self) -> None:
        """No cleanup needed for CSV storage."""
        pass


class ORMStorage(StorageAdapter):
    """Store responses using SQLAlchemy ORM with proper models.

    Provides type-safe ORM-based persistence using SQLAlchemy declarative models.
    Benefits from relationship mapping, query builder capabilities, and support
    for Alembic migrations for schema evolution.

    Args:
        db_url: PostgreSQL connection string (e.g., postgresql://user:pass@host/db)

    Attributes:
        engine: SQLAlchemy Engine instance
        Session: Sessionmaker bound to the engine

    Thread-Safety: Not thread-safe for concurrent writes. Use a connection pool
        or create separate ORMStorage instances for concurrent access.

    Example:
        >>> storage = ORMStorage("postgresql://localhost/qualer")
        >>> storage.store_response(
        ...     url="https://api.example.com/clients",
        ...     service="client_information",
        ...     method="GET",
        ...     request_headers={"User-Agent": "python"},
        ...     response_body='{"id": 1, "name": "Client A"}',
        ...     response_headers={"Content-Type": "application/json"}
        ... )
        >>> storage.close()
    """

    def __init__(self, db_url: str) -> None:
        """Initialize ORM storage with database connection.

        Args:
            db_url: PostgreSQL connection string

        Raises:
            sqlalchemy.exc.ArgumentError: If db_url is invalid
        """
        from sqlalchemy.orm import sessionmaker

        from .models import Base

        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

        # Ensure tables exist
        Base.metadata.create_all(self.engine)

    def store_response(
        self,
        url: str,
        service: str,
        method: str,
        request_headers: Optional[dict],
        response_body: Optional[str],
        response_headers: Optional[dict],
    ) -> None:
        """Store API response using ORM model.

        Automatically handles duplicate detection via unique constraint.
        Stores dict headers directly as JSONB (no extra serialization).

        Args:
            url: API endpoint URL
            service: Service/endpoint name
            method: HTTP method (GET, POST, etc.)
            request_headers: Request headers dict
            response_body: Response body text/JSON
            response_headers: Response headers dict

        Raises:
            sqlalchemy.exc.IntegrityError: If unique constraint violated
                (handled by ON CONFLICT logic in database)
        """
        from .models import APIResponse

        session = self.Session()
        try:
            # Create ORM model instance
            # Note: JSONB columns accept dicts directly; SQLAlchemy handles serialization
            response = APIResponse(
                url=url,
                service=service,
                method=method,
                request_header=request_headers,  # Pass dict directly, JSONB handles it
                response_body=response_body,
                response_header=response_headers,  # Pass dict directly, JSONB handles it
                parsed=False,
            )

            session.add(response)
            session.commit()
        except Exception as e:
            session.rollback()
            # Gracefully handle duplicate key errors (409 Conflict)
            if "unique constraint" in str(e).lower():
                pass  # Duplicate - expected for idempotent operations
            else:
                raise
        finally:
            session.close()

    def close(self) -> None:
        """Close database connection and cleanup resources.

        Disposes of the engine's connection pool.
        """
        if self.engine:
            self.engine.dispose()
