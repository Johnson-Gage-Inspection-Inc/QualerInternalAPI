"""Tests for storage adapters."""

import pytest
import json
import os
import csv
import tempfile
from pathlib import Path
from persistence.storage import PostgresRawStorage, CSVStorage, StorageAdapter
from sqlalchemy import create_engine, text


class TestPostgresRawStorage:
    """Tests for PostgresRawStorage adapter."""

    def test_store_response_success(self, db_url):
        """Test storing a response in PostgreSQL."""
        storage = PostgresRawStorage(db_url)
        
        try:
            storage.store_response(
                url="https://example.com/api/test",
                service="TestService",
                method="GET",
                request_headers={"Authorization": "Bearer token"},
                response_body='{"status": "ok"}',
                response_headers={"Content-Type": "application/json"},
            )
            
            # Verify data was stored
            engine = create_engine(db_url)
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT * FROM datadump WHERE service = :service"),
                    {"service": "TestService"}
                )
                rows = result.fetchall()
                assert len(rows) == 1
                assert rows[0].url == "https://example.com/api/test"
                assert rows[0].method == "GET"
                assert rows[0].response_body == '{"status": "ok"}'
            engine.dispose()
        finally:
            storage.close()

    def test_store_response_conflict_handling(self, db_url):
        """Test that duplicate entries are handled via ON CONFLICT."""
        storage = PostgresRawStorage(db_url)
        
        try:
            # Store same response twice
            for i in range(2):
                storage.store_response(
                    url="https://example.com/api/duplicate",
                    service="DuplicateTest",
                    method="POST",
                    request_headers={},
                    response_body=f"Response {i}",
                    response_headers={},
                )
            
            # Verify only one entry exists (first one wins)
            engine = create_engine(db_url)
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT COUNT(*) as cnt FROM datadump WHERE service = :service"),
                    {"service": "DuplicateTest"}
                )
                count = result.fetchone().cnt
                assert count == 1
                
                # Verify it's the first response
                result = conn.execute(
                    text("SELECT response_body FROM datadump WHERE service = :service"),
                    {"service": "DuplicateTest"}
                )
                body = result.fetchone().response_body
                assert body == "Response 0"
            engine.dispose()
        finally:
            storage.close()

    def test_run_sql(self, db_url):
        """Test backwards compatibility run_sql method."""
        storage = PostgresRawStorage(db_url)
        
        try:
            # Insert test data
            storage.store_response(
                url="https://example.com/api/sql_test",
                service="SQLTest",
                method="GET",
                request_headers={},
                response_body="test body",
                response_headers={},
            )
            
            # Query using run_sql
            results = storage.run_sql(
                "SELECT * FROM datadump WHERE service = :service",
                {"service": "SQLTest"}
            )
            assert len(results) == 1
            assert results[0].url == "https://example.com/api/sql_test"
        finally:
            storage.close()

    def test_close_disposes_engine(self, db_url):
        """Test that close() properly disposes the engine."""
        storage = PostgresRawStorage(db_url)
        assert not storage._disposed
        
        storage.close()
        assert storage._disposed
        
        # Verify operations fail after close
        with pytest.raises(RuntimeError, match="has been disposed"):
            storage.store_response(
                url="https://example.com/api/fail",
                service="FailTest",
                method="GET",
                request_headers={},
                response_body="should fail",
                response_headers={},
            )

    def test_multiple_close_calls_safe(self, db_url):
        """Test that calling close() multiple times is safe."""
        storage = PostgresRawStorage(db_url)
        storage.close()
        storage.close()  # Should not raise
        assert storage._disposed


class TestCSVStorage:
    """Tests for CSVStorage adapter."""

    def test_store_response_creates_file(self):
        """Test that storing a response creates a CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = CSVStorage(output_dir=tmpdir)
            
            storage.store_response(
                url="https://example.com/api/test",
                service="TestService",
                method="GET",
                request_headers={"Authorization": "Bearer token"},
                response_body='{"status": "ok"}',
                response_headers={"Content-Type": "application/json"},
            )
            
            csv_path = Path(tmpdir) / "TestService.csv"
            assert csv_path.exists()
            
            # Verify CSV content
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]["url"] == "https://example.com/api/test"
                assert rows[0]["method"] == "GET"
                assert rows[0]["response_body"] == '{"status": "ok"}'
            
            storage.close()

    def test_store_response_appends_to_existing_file(self):
        """Test that storing multiple responses appends to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = CSVStorage(output_dir=tmpdir)
            
            # Store two responses
            for i in range(2):
                storage.store_response(
                    url=f"https://example.com/api/test{i}",
                    service="AppendTest",
                    method="GET",
                    request_headers={},
                    response_body=f"Response {i}",
                    response_headers={},
                )
            
            csv_path = Path(tmpdir) / "AppendTest.csv"
            
            # Verify both rows exist
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]["response_body"] == "Response 0"
                assert rows[1]["response_body"] == "Response 1"
            
            storage.close()

    def test_csv_injection_prevention(self):
        """Test that CSV injection attacks are prevented via quoting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = CSVStorage(output_dir=tmpdir)
            
            # Try to inject malicious content
            malicious_content = '=1+1","=cmd|/C calc"'
            storage.store_response(
                url="https://example.com/api/injection",
                service="InjectionTest",
                method="POST",
                request_headers={},
                response_body=malicious_content,
                response_headers={},
            )
            
            csv_path = Path(tmpdir) / "InjectionTest.csv"
            
            # Verify content is properly quoted/escaped
            with open(csv_path, "r", encoding="utf-8") as f:
                content = f.read()
                # With QUOTE_ALL, all fields should be quoted
                assert '"' in content
                
                # Parse and verify the malicious content is treated as data
                f.seek(0)
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]["response_body"] == malicious_content
            
            storage.close()

    def test_handles_special_characters(self):
        """Test that special characters (newlines, quotes, commas) are handled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = CSVStorage(output_dir=tmpdir)
            
            special_response = 'Line 1\nLine 2\n"Quoted"\nComma, separated'
            storage.store_response(
                url="https://example.com/api/special",
                service="SpecialCharsTest",
                method="GET",
                request_headers={"key": "value with, comma"},
                response_body=special_response,
                response_headers={"header": 'value with "quotes"'},
            )
            
            csv_path = Path(tmpdir) / "SpecialCharsTest.csv"
            
            # Verify content is preserved correctly
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]["response_body"] == special_response
                
                # Verify JSON-encoded headers preserve special chars
                req_headers = json.loads(rows[0]["request_headers"])
                assert req_headers["key"] == "value with, comma"
                
                res_headers = json.loads(rows[0]["response_headers"])
                assert res_headers["header"] == 'value with "quotes"'
            
            storage.close()

    def test_creates_output_directory(self):
        """Test that output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / "nested" / "subdir"
            assert not nested_dir.exists()
            
            storage = CSVStorage(output_dir=str(nested_dir))
            assert nested_dir.exists()
            
            storage.close()

    def test_close_is_idempotent(self):
        """Test that close() can be called multiple times safely."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = CSVStorage(output_dir=tmpdir)
            storage.close()
            storage.close()  # Should not raise


class TestStorageAdapterInterface:
    """Tests for the StorageAdapter abstract interface."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that StorageAdapter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            StorageAdapter()  # type: ignore

    def test_concrete_implementations_must_implement_methods(self):
        """Test that concrete classes must implement all abstract methods."""
        # Create an incomplete implementation
        class IncompleteStorage(StorageAdapter):
            def store_response(self, *args, **kwargs):
                pass
            # Missing close() method
        
        with pytest.raises(TypeError):
            IncompleteStorage()  # type: ignore
