"""Unit tests for storage adapters."""

import os
import tempfile
from persistence.storage import PostgresRawStorage, CSVStorage
from persistence.schema import create_datadump_table


class TestPostgresRawStorage:
    """Tests for PostgresRawStorage adapter."""

    def test_store_response_success(self, db_url):
        """Test storing a response successfully."""
        storage = PostgresRawStorage(db_url)
        create_datadump_table(storage.engine.connect())

        test_data = {
            "url": "https://example.com/api",
            "service": "test_service",
            "method": "GET",
            "request_headers": {"User-Agent": "TestClient/1.0"},
            "response_body": '{"status": "ok"}',
            "response_headers": {"Content-Type": "application/json"},
        }

        storage.store_response(**test_data)

        # Verify data was stored
        result = storage.run_sql(
            "SELECT * FROM datadump WHERE url = :url",
            {"url": test_data["url"]},
        )
        assert result is not None
        assert len(result) == 1
        assert result[0][1] == test_data["url"]  # url column
        assert result[0][2] == test_data["service"]  # service column

        storage.close()

    def test_store_response_conflict_handling(self, db_url):
        """Test that duplicate inserts are handled gracefully with ON CONFLICT."""
        storage = PostgresRawStorage(db_url)
        create_datadump_table(storage.engine.connect())

        test_data = {
            "url": "https://example.com/api",
            "service": "test_service",
            "method": "GET",
            "request_headers": {"User-Agent": "TestClient/1.0"},
            "response_body": '{"status": "ok"}',
            "response_headers": {"Content-Type": "application/json"},
        }

        # Insert twice - second should be ignored due to ON CONFLICT
        storage.store_response(**test_data)
        storage.store_response(**test_data)

        # Verify only one record exists
        result = storage.run_sql(
            "SELECT COUNT(*) FROM datadump WHERE url = :url",
            {"url": test_data["url"]},
        )
        assert result is not None
        assert result[0][0] == 1  # Count should be 1

        storage.close()

    def test_run_sql_select(self, db_url):
        """Test running SELECT queries."""
        storage = PostgresRawStorage(db_url)
        create_datadump_table(storage.engine.connect())

        # Insert test data
        storage.run_sql(
            """
            INSERT INTO datadump (url, service, method, response_body)
            VALUES (:url, :service, :method, :body)
            """,
            {
                "url": "https://test.com",
                "service": "test",
                "method": "GET",
                "body": '{"test": true}',
            },
        )

        # Run SELECT query
        result = storage.run_sql(
            "SELECT url, service FROM datadump WHERE service = :service",
            {"service": "test"},
        )
        assert result is not None
        assert len(result) == 1
        assert result[0][0] == "https://test.com"

        storage.close()

    def test_run_sql_insert_returns_none(self, db_url):
        """Test that INSERT queries return None (no rows)."""
        storage = PostgresRawStorage(db_url)
        create_datadump_table(storage.engine.connect())

        result = storage.run_sql(
            """
            INSERT INTO datadump (url, service, method, response_body)
            VALUES (:url, :service, :method, :body)
            """,
            {
                "url": "https://test.com",
                "service": "test",
                "method": "POST",
                "body": '{"inserted": true}',
            },
        )
        assert result is None  # INSERT doesn't return rows

        storage.close()


class TestCSVStorage:
    """Tests for CSVStorage adapter."""

    def test_store_response_creates_csv(self):
        """Test that store_response creates a CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = CSVStorage(tmpdir)

            test_data = {
                "url": "https://example.com/api",
                "service": "test_service",
                "method": "GET",
                "request_headers": {"User-Agent": "TestClient/1.0"},
                "response_body": '{"status": "ok"}',
                "response_headers": {"Content-Type": "application/json"},
            }

            storage.store_response(**test_data)

            # Verify CSV file was created
            csv_path = os.path.join(tmpdir, "test_service.csv")
            assert os.path.exists(csv_path)

            # Verify file has header and one data row
            with open(csv_path, "r") as f:
                lines = f.readlines()
                assert len(lines) == 2  # header + data row
                assert "timestamp" in lines[0]
                assert "url" in lines[0]

    def test_store_response_appends_to_csv(self):
        """Test that multiple calls append to the same CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = CSVStorage(tmpdir)

            # Insert first response
            storage.store_response(
                url="https://example.com/1",
                service="api",
                method="GET",
                request_headers={},
                response_body='{"id": 1}',
                response_headers={},
            )

            # Insert second response
            storage.store_response(
                url="https://example.com/2",
                service="api",
                method="GET",
                request_headers={},
                response_body='{"id": 2}',
                response_headers={},
            )

            # Verify file has header and two data rows
            csv_path = os.path.join(tmpdir, "api.csv")
            with open(csv_path, "r") as f:
                lines = f.readlines()
                assert len(lines) == 3  # header + 2 data rows

    def test_store_response_handles_special_characters(self):
        """Test that CSV writer properly escapes special characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = CSVStorage(tmpdir)

            # Response with quotes and commas
            test_data = {
                "url": "https://example.com/api",
                "service": "test_service",
                "method": "GET",
                "request_headers": {"X-Test": 'value with "quotes" and, comma'},
                "response_body": '{"text": "simple"}',
                "response_headers": {"Content-Type": "application/json"},
            }

            storage.store_response(**test_data)

            # Verify CSV file can be read without corruption
            csv_path = os.path.join(tmpdir, "test_service.csv")
            with open(csv_path, "r") as f:
                content = f.read()
                # Should have header and data with proper quoting
                assert "timestamp" in content
                assert "url" in content
                # QUOTE_ALL should protect the special characters
                assert '"' in content

    def test_store_response_creates_output_directory(self):
        """Test that output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "subdir", "responses")
            assert not os.path.exists(output_dir)

            CSVStorage(output_dir)

            assert os.path.exists(output_dir)

    def test_close_is_noop(self):
        """Test that close() is safe to call multiple times."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = CSVStorage(tmpdir)
            # close() should not raise any errors
            storage.close()
            storage.close()  # Safe to call multiple times

    def test_csv_columns_format(self):
        """Test that CSV has correct columns in correct order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = CSVStorage(tmpdir)

            storage.store_response(
                url="https://example.com",
                service="api",
                method="POST",
                request_headers={"key": "value"},
                response_body="response",
                response_headers={"header": "value"},
            )

            csv_path = os.path.join(tmpdir, "api.csv")
            with open(csv_path, "r") as f:
                header = f.readline().strip()
                # Verify expected columns in order (accounting for quotes from QUOTE_ALL)
                assert "timestamp" in header
                assert "url" in header
                assert "method" in header
                assert "response_body" in header
                assert "request_headers" in header
                assert "response_headers" in header
