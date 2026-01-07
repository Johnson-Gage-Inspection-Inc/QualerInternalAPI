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
        self.engine: Optional[Engine] = create_engine(db_url)

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
        if not self.engine:
            raise RuntimeError("Storage engine not initialized")

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
                        :req_headers, :res_body, :res_headers
                    )
                    ON CONFLICT (url, service, method) DO NOTHING
                    """
                ),
                {
                    "url": url,
                    "service": service,
                    "method": method,
                    "req_headers": request_headers,
                    "res_body": response_body,
                    "res_headers": response_headers,
                },
            )

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
        if self.engine:
            self.engine.dispose()
            self.engine = None


class CSVStorage(StorageAdapter):
    """
    Stores API responses as CSV files (for ad-hoc analysis).

    Creates one CSV file per service with columns:
        timestamp, url, method, status_code, response_body

    Useful for quick data exploration without database overhead.
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
            writer = csv.writer(f)

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
