"""Database schema definitions for shared use by application and tests."""

from sqlalchemy import text
from sqlalchemy.engine import Connection


def create_datadump_table(conn: Connection) -> None:
    """
    Create the datadump table for storing raw API responses.
    
    This table is used by PostgresRawStorage to store responses as-is
    for later parsing and processing.
    
    Schema:
        - id: Auto-incrementing primary key
        - url, service, method: Composite unique key for idempotent storage
        - request_header, response_header: JSONB for structured headers
        - response_body: TEXT for raw response content
        - parsed: BOOLEAN flag for downstream processing
        - created_at: Timestamp of record creation
    
    Args:
        conn: SQLAlchemy connection object (within a transaction)
    """
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS datadump (
                id SERIAL PRIMARY KEY,
                url TEXT NOT NULL,
                service TEXT NOT NULL,
                method TEXT NOT NULL,
                request_header JSONB,
                response_body TEXT,
                response_header JSONB,
                parsed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(url, service, method)
            )
        """
        )
    )
