"""Pytest configuration and fixtures."""

import pytest
import os
import time


@pytest.fixture(scope="session")
def _postgres_container_session():
    """Start PostgreSQL container once per session."""
    # Use fixed database on port 5433
    connection_url = "postgresql://postgres:postgres@localhost:5433/test_qualer"

    # Wait for database to be ready with retries
    max_retries = 10
    retry_delay = 1
    for attempt in range(max_retries):
        try:
            from sqlalchemy import create_engine, text

            engine = create_engine(connection_url)
            with engine.begin() as conn:
                conn.execute(text("SELECT 1"))
            engine.dispose()
            break  # Connection successful
        except Exception as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Database not ready after {max_retries} retries: {e}")
            time.sleep(retry_delay)

    # Enable hstore extension
    from sqlalchemy import create_engine, text

    engine = create_engine(connection_url)
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS hstore"))
    engine.dispose()

    yield connection_url


@pytest.fixture
def postgres_container(_postgres_container_session):
    """
    Provide a clean PostgreSQL database for each test.

    Cleans up tables before each test to ensure isolated test state.
    """
    # Skip if running without database tests
    if os.getenv("SKIP_DB_TESTS"):
        pytest.skip("Database tests disabled")

    connection_url = _postgres_container_session

    # Set up clean database schema for this test
    from sqlalchemy import create_engine, text
    from persistence.schema import create_datadump_table

    engine = create_engine(connection_url)

    with engine.begin() as conn:
        # Enable hstore extension for datadump table
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS hstore"))
        # Drop and recreate tables for clean test state
        conn.execute(text("DROP TABLE IF EXISTS api_response CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS datadump CASCADE"))
        # Create datadump table (used by PostgresRawStorage)
        create_datadump_table(conn)

    engine.dispose()

    yield connection_url


@pytest.fixture
def db_url(postgres_container):
    """Provide database URL from testcontainer."""
    return postgres_container
