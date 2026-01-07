"""Storage adapters for API responses - supports PostgreSQL, CSV, and future ORM."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import json
import os
import csv
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


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
        pass

    @abstractmethod
    def close(self) -> None:
        """Clean up resources."""
        pass


class PostgresRawStorage(StorageAdapter):
    """
    Stores raw API responses in PostgreSQL datadump table.

    This is the "raw staging" layer - responses are stored as-is for later parsing.
    Schema:
        - url, service, method (composite unique key)
        - request_header, response_header (JSONB)
        - response_body (TEXT)
        - parsed (BOOLEAN) - flag for downstream processing
    """

    def __init__(self, db_url: str):
        """
        Initialize PostgreSQL storage.

        Args:
            db_url: PostgreSQL connection string (e.g., postgresql://user:pass@host/db)
        """
        self.engine: Engine = create_engine(db_url)
        self._disposed = False

    def store_response(
        self,
        url: str,
        service: str,
        method: str,
        request_headers: Dict[str, Any],
        response_body: str,
        response_headers: Dict[str, Any],
    ) -> None:
        """Store response in datadump table with conflict handling."""
        if self._disposed:
            raise RuntimeError("Storage engine has been disposed")

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
                    ON CONFLICT (url, service, method) DO NOTHING
                    """
                ),
                {
                    "url": url,
                    "service": service,
                    "method": method,
                    "req_headers": json.dumps(request_headers),
                    "res_body": response_body,
                    "res_headers": json.dumps(response_headers),
                },
            )

    def run_sql(self, sql_query: str, params: Optional[Dict] = None):
        """Execute arbitrary SQL query (for backwards compatibility)."""
        if self._disposed:
            raise RuntimeError("Storage engine has been disposed")
        with self.engine.connect() as conn:
            result = conn.execute(text(sql_query), params or {})
            return result.fetchall()

    def close(self) -> None:
        """Dispose of SQLAlchemy engine."""
        if not self._disposed:
            self.engine.dispose()
            self._disposed = True


class CSVStorage(StorageAdapter):
    """
    Stores API responses as CSV files (for ad-hoc analysis).

    Creates one CSV file per service with columns:
        timestamp, url, method, response_body, request_headers, response_headers

    Useful for quick data exploration without database overhead.
    Note: This implementation is not thread-safe. Use separate instances
    for concurrent access or implement file locking if needed.
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
            # Use QUOTE_ALL to prevent CSV injection attacks
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


# Future: SQLAlchemy ORM storage with Alembic migrations
# class ORMStorage(StorageAdapter):
#     """
#     Stores responses using SQLAlchemy ORM with proper models.
#
#     Benefits:
#     - Type safety
#     - Relationship mapping
#     - Alembic migrations for schema evolution
#     - Query builder instead of raw SQL
#     """
#     def __init__(self, db_url: str):
#         from .models import APIResponse  # Import ORM model
#         self.engine = create_engine(db_url)
#         self.Session = sessionmaker(bind=self.engine)
#
#     def store_response(self, ...):
#         session = self.Session()
#         response = APIResponse(
#             url=url, service=service, method=method,
#             request_headers=request_headers,
#             response_body=response_body,
#             response_headers=response_headers
#         )
#         session.add(response)
#         session.commit()
