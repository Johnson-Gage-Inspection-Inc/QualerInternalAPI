"""HTML parsing utilities for Qualer data extraction."""

from typing import Any, Dict
from bs4 import BeautifulSoup


def extract_form_fields(html: str, form_id: str) -> Dict[str, Any]:
    """
    Extract all input fields from an HTML form by its ID.

    Parses an HTML document using BeautifulSoup, finds the form with the
    specified ID, and extracts all input field names and values.

    Args:
        html: The HTML content to parse
        form_id: The ID of the form to extract fields from

    Returns:
        Dictionary mapping field names to their values.
        Returns empty dict if form not found.

    Example:
        >>> html = '<form id="MyForm"><input name="field1" value="value1"></form>'
        >>> extract_form_fields(html, "MyForm")
        {'field1': 'value1'}
    """
    soup = BeautifulSoup(html, "html.parser")
    form_data: Dict[str, Any] = {}

    form = soup.find("form", {"id": form_id})
    if not form:
        return form_data

    # Extract all input fields from the form
    for input_field in form.find_all("input"):
        name = input_field.get("name")
        value = input_field.get("value", "")

        # Only add if name is a valid string
        if name and isinstance(name, str):
            form_data[name] = value

    return form_data


def extract_form_fields_safe(
    html: str, form_id: str, fallback_length: int = 1000
) -> Dict[str, Any]:
    """
    Extract form fields with fallback to raw HTML snippet if form not found.

    Useful for debugging—returns a snippet of the raw HTML response if the
    expected form cannot be found.

    Args:
        html: The HTML content to parse
        form_id: The ID of the form to extract fields from
        fallback_length: Number of characters to include in fallback response

    Returns:
        Dictionary with parsed form fields, or {"raw_response": html_snippet}
        if the form is not found.

    Example:
        >>> result = extract_form_fields_safe(html, "ClientInformation")
        >>> if "raw_response" in result:
        ...     print("Form not found. First 1000 chars:", result["raw_response"])
    """
    form_data = extract_form_fields(html, form_id)

    if not form_data:
        return {"raw_response": html[:fallback_length]}

    return form_data
