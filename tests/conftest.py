"""Pytest configuration and fixtures."""

import pytest
import os
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres_container():
    """
    Provide a PostgreSQL testcontainer for tests requiring a database.

    The container is started once per test session and cleaned up automatically.
    Tests can access the connection URL via the fixture.
    """
    # Skip if running without database tests
    if os.getenv("SKIP_DB_TESTS"):
        pytest.skip("Database tests disabled")

    with PostgresContainer("postgres:16") as postgres:
        # Set up database schema
        connection_url = postgres.get_connection_url()

        # Create tables needed for tests
        from sqlalchemy import create_engine, text

        engine = create_engine(connection_url)

        with engine.begin() as conn:
            # Create datadump table (used by PostgresRawStorage)
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

        engine.dispose()

        yield connection_url


@pytest.fixture
def db_url(postgres_container):
    """Provide database URL from testcontainer."""
    return postgres_container
