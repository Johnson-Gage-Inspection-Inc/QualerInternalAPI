"""Database schema definitions shared across application and tests."""

from sqlalchemy import text

# Datadump table schema - raw staging layer for API responses
DATADUMP_SCHEMA = """
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


def create_datadump_table(conn) -> None:
    """
    Create the datadump table using the standard schema.

    Args:
        conn: SQLAlchemy connection object
    """
    conn.execute(text(DATADUMP_SCHEMA))


__all__ = ["DATADUMP_SCHEMA", "create_datadump_table"]
