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

    # Set up clean database schema for this test using Alembic
    from sqlalchemy import create_engine, text
    from alembic import command
    from alembic.config import Config

    engine = create_engine(connection_url)

    with engine.begin() as conn:
        # Drop all tables for clean state
        conn.execute(text("DROP TABLE IF EXISTS datadump CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))

    engine.dispose()

    # Run Alembic migrations to create fresh schema
    import pathlib

    project_root = pathlib.Path(__file__).parent.parent
    alembic_ini_path = project_root / "alembic.ini"

    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("sqlalchemy.url", connection_url)

    # Stamp the database as being at "base" (no migrations) so upgrade works
    command.stamp(alembic_cfg, "base")
    # Now run all migrations
    command.upgrade(alembic_cfg, "head")

    yield connection_url


@pytest.fixture
def db_url(postgres_container):
    """Provide database URL from testcontainer."""
    return postgres_container


def pytest_collection_modifyitems(config, items):
    """Auto-apply postgres_container fixture to tests marked with @pytest.mark.database."""
    for item in items:
        if item.get_closest_marker("database"):
            item.fixturenames.append("postgres_container")
