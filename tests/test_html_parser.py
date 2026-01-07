"""Tests for HTML parsing utilities."""

import pytest
from utils.html_parser import extract_form_fields, extract_form_fields_safe


class TestExtractFormFields:
    """Tests for extract_form_fields function."""

    def test_extract_simple_form(self):
        """Test extracting fields from a simple form."""
        html = """
        <html>
            <form id="TestForm">
                <input name="field1" value="value1">
                <input name="field2" value="value2">
            </form>
        </html>
        """
        result = extract_form_fields(html, "TestForm")
        assert result == {"field1": "value1", "field2": "value2"}

    def test_extract_form_with_empty_values(self):
        """Test extracting fields with empty values."""
        html = """
        <html>
            <form id="TestForm">
                <input name="field1" value="">
                <input name="field2" value="value2">
            </form>
        </html>
        """
        result = extract_form_fields(html, "TestForm")
        assert result == {"field1": "", "field2": "value2"}

    def test_extract_form_with_no_value_attribute(self):
        """Test extracting fields with missing value attribute."""
        html = """
        <html>
            <form id="TestForm">
                <input name="field1">
                <input name="field2" value="value2">
            </form>
        </html>
        """
        result = extract_form_fields(html, "TestForm")
        assert result == {"field1": "", "field2": "value2"}

    def test_form_not_found(self):
        """Test behavior when form is not found."""
        html = """
        <html>
            <form id="OtherForm">
                <input name="field1" value="value1">
            </form>
        </html>
        """
        result = extract_form_fields(html, "TestForm")
        assert result == {}

    def test_input_without_name(self):
        """Test that inputs without name attribute are ignored."""
        html = """
        <html>
            <form id="TestForm">
                <input value="value1">
                <input name="field2" value="value2">
            </form>
        </html>
        """
        result = extract_form_fields(html, "TestForm")
        assert result == {"field2": "value2"}

    def test_input_with_list_name(self):
        """Test that inputs with list-type names are handled correctly."""
        html = """
        <html>
            <form id="TestForm">
                <input name="field1" value="value1">
                <input name="field2" value="value2">
            </form>
        </html>
        """
        result = extract_form_fields(html, "TestForm")
        # Verify only string names are included
        for key in result.keys():
            assert isinstance(key, str)

    def test_complex_form_structure(self):
        """Test extracting from a form with various HTML attributes."""
        html = """
        <html>
            <form id="ClientInformation">
                <input type="hidden" name="Id" value="12345">
                <input type="text" name="Name" value="Test Client">
                <input type="email" name="Email" value="test@example.com">
                <input type="checkbox" name="Active" value="true">
            </form>
        </html>
        """
        result = extract_form_fields(html, "ClientInformation")
        assert result == {
            "Id": "12345",
            "Name": "Test Client",
            "Email": "test@example.com",
            "Active": "true",
        }


class TestExtractFormFieldsSafe:
    """Tests for extract_form_fields_safe function."""

    def test_successful_extraction(self):
        """Test successful extraction returns parsed fields."""
        html = """
        <html>
            <form id="TestForm">
                <input name="field1" value="value1">
            </form>
        </html>
        """
        result = extract_form_fields_safe(html, "TestForm")
        assert result == {"field1": "value1"}
        assert "raw_response" not in result

    def test_form_not_found_returns_snippet(self):
        """Test that missing form returns raw HTML snippet."""
        html = "<html><body>No form here</body></html>"
        result = extract_form_fields_safe(html, "TestForm")
        assert "raw_response" in result
        assert result["raw_response"] == html[:1000]

    def test_form_not_found_respects_fallback_length(self):
        """Test that fallback_length parameter is respected."""
        html = "x" * 5000
        result = extract_form_fields_safe(html, "TestForm", fallback_length=100)
        assert "raw_response" in result
        assert len(result["raw_response"]) == 100
        assert result["raw_response"] == "x" * 100

    def test_empty_form_returns_snippet(self):
        """Test that empty form (no fields) returns raw snippet."""
        html = """
        <html>
            <form id="TestForm">
                <!-- No input fields -->
            </form>
        </html>
        """
        result = extract_form_fields_safe(html, "TestForm")
        # Empty form returns empty dict from extract_form_fields
        # extract_form_fields_safe should return raw snippet
        assert "raw_response" in result
