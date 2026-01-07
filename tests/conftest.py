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
        from sqlalchemy import create_engine
        from persistence.schema import create_datadump_table

        engine = create_engine(connection_url)

        with engine.begin() as conn:
            # Create datadump table (used by PostgresRawStorage)
            create_datadump_table(conn)

        engine.dispose()

        yield connection_url


@pytest.fixture
def db_url(postgres_container):
    """Provide database URL from testcontainer."""
    return postgres_container
