"""Tests for CSRF token extraction in QualerAPIFetcher."""

import pytest
from utils.auth import QualerAPIFetcher


class TestExtractCSRFToken:
    """Tests for extract_csrf_token method."""

    def test_extract_token_name_before_value(self):
        """Test extraction when name attribute comes before value."""
        html = """
        <html>
            <form>
                <input type="hidden" name="__RequestVerificationToken" value="test-token-123">
            </form>
        </html>
        """
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        token = fetcher.extract_csrf_token(html)
        assert token == "test-token-123"

    def test_extract_token_value_before_name(self):
        """Test extraction when value attribute comes before name."""
        html = """
        <html>
            <form>
                <input type="hidden" value="test-token-456" name="__RequestVerificationToken">
            </form>
        </html>
        """
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        token = fetcher.extract_csrf_token(html)
        assert token == "test-token-456"

    def test_extract_token_with_other_attributes(self):
        """Test extraction with additional attributes between name and value."""
        html = """
        <html>
            <form>
                <input type="hidden" name="__RequestVerificationToken" id="csrf-field" class="hidden" value="test-token-789">
            </form>
        </html>
        """
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        token = fetcher.extract_csrf_token(html)
        assert token == "test-token-789"

    def test_extract_token_minified_html(self):
        """Test extraction from minified HTML (no spaces)."""
        html = '<input type="hidden" name="__RequestVerificationToken" value="minified-token-abc">'
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        token = fetcher.extract_csrf_token(html)
        assert token == "minified-token-abc"

    def test_extract_token_with_complex_value(self):
        """Test extraction with a complex token value (base64-like)."""
        html = """
        <input name="__RequestVerificationToken" value="CfDJ8NvE3x5aBC123+DEF456/GHI789==">
        """
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        token = fetcher.extract_csrf_token(html)
        assert token == "CfDJ8NvE3x5aBC123+DEF456/GHI789=="

    def test_extract_token_multiple_inputs(self):
        """Test extraction when multiple input fields exist."""
        html = """
        <html>
            <form>
                <input name="username" value="user">
                <input name="__RequestVerificationToken" value="correct-token">
                <input name="password" value="pass">
            </form>
        </html>
        """
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        token = fetcher.extract_csrf_token(html)
        assert token == "correct-token"

    def test_token_not_found_raises_error(self):
        """Test that ValueError is raised when token is not found."""
        html = """
        <html>
            <form>
                <input name="username" value="user">
            </form>
        </html>
        """
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        with pytest.raises(ValueError, match="Could not find CSRF token"):
            fetcher.extract_csrf_token(html)

    def test_token_with_single_quotes(self):
        """Test extraction when attributes use single quotes."""
        html = """
        <input name='__RequestVerificationToken' value='single-quote-token'>
        """
        # This test documents current behavior - regex expects double quotes
        # If single quotes need to be supported, the regex would need updating
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        with pytest.raises(ValueError):
            fetcher.extract_csrf_token(html)

    def test_extract_first_token_if_multiple(self):
        """Test that first token is extracted when multiple exist."""
        html = """
        <html>
            <form>
                <input name="__RequestVerificationToken" value="first-token">
                <input name="__RequestVerificationToken" value="second-token">
            </form>
        </html>
        """
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        token = fetcher.extract_csrf_token(html)
        # Should match the first occurrence
        assert token == "first-token"

    def test_non_greedy_matching(self):
        """Test that regex uses non-greedy matching to avoid crossing input tags."""
        html = """
        <input name="field1" value="value1"><input name="__RequestVerificationToken" value="target-token"><input name="field2" value="value2">
        """
        fetcher = QualerAPIFetcher.__new__(QualerAPIFetcher)
        token = fetcher.extract_csrf_token(html)
        assert token == "target-token"
        # Verify it doesn't accidentally match across multiple input elements
        assert "value1" not in token
        assert "value2" not in token
