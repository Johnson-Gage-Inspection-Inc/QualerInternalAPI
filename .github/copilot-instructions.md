# Copilot Instructions for QualerInternalAPI

## Project Overview
QualerInternalAPI is a Python-based data extraction pipeline for the Qualer quality management system. It fetches client and service data from the Qualer web application, parses HTML responses, and stores results in multiple formats (JSON, CSV, PostgreSQL).

## Architecture & Key Components

### Core Authentication Pattern
**Pattern**: `QualerAPIFetcher` (context manager in `my_qualer_utils.py`)
- Handles browser automation via Selenium for Qualer login
- Automatically extracts authenticated cookies into a `requests.Session`
- Provides both DB access (SQLAlchemy) and HTTP access (requests)
- **Always use as context manager**: `with QualerAPIFetcher() as fetcher: ...`
- Credentials: `QUALER_USERNAME`/`QUALER_PASSWORD` env vars or interactive prompt
- Cleans up Selenium driver automatically on exit

### Data Extraction Pattern
1. **Fetch HTML** - Use authenticated session to GET endpoint
2. **Parse with BeautifulSoup** - Find form by ID and extract `<input>` fields
3. **Extract Values** - Return dict of `{field_name: field_value}`
4. **Bulk Processing** - Reuse single session for multiple requests (avoid re-auth per request)

Example: `getClientInformation.py` - fetches all client HTML forms, parses with BeautifulSoup, outputs JSON + CSV

### API Client (Qualer SDK)
- **Location**: `integrations/qualer_sdk/client.py`
- **Pattern**: Singleton with thread-safe lazy initialization
- **Usage**: `from integrations.qualer_sdk.client import make_qualer_client`
- **Requires**: `QUALER_API_KEY` env var
- **Note**: Prefer for structured API endpoints; use `QualerAPIFetcher` for HTML scraping

## Development Workflows

### Running Scripts
```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run individual extraction script (prompts for credentials)
python.exe getClientInformation.py

# With environment variables pre-set
$env:QUALER_USERNAME="user@jgiquality.com"; python.exe getClientInformation.py
```

### Testing
- **Location**: `tests/test_getClientInformation.py`
- **Framework**: pytest (installed in requirements.txt)
- **Mock Pattern**: Use `unittest.mock` to patch `requests.Session.get` for HTTP testing
- **Run**: `pytest tests/`

### Linting & Type Checking
- **Flake8**: Configured to ignore E501 (line length) via `.flake8`
- **MyPy**: Basic type checking (ignores missing stubs) via `mypy.ini`
- **Run**: `flake8 .` or `mypy .` (manual; not automated)

## Project-Specific Conventions

### Session Management
- **Critical**: Reuse authenticated sessions across multiple requests
- **Anti-pattern**: Calling `get_client_information_with_auth(id)` in a loop (re-authenticates each time)
- **Pattern**: Use single `QualerAPIFetcher` context, pass `session` param to fetch functions

### HTML Parsing
- Always use BeautifulSoup with `html.parser` parser
- Extract input fields via `form.find_all("input")` - check `name` and `value` attributes
- Fallback gracefully if form not found (return warning dict, not exception)
- Handle field values that are lists: `isinstance(name, str)` before using as dict key

### Error Handling
- **403 Forbidden**: Skip gracefully in bulk operations (permission denied for that client)
- **Empty responses**: Return `{"raw_response": text[:1000]}` for debugging
- **Credentials**: Always prompt with `getpass()` for passwords (never in CLI args)

### Output Format
- **JSON**: Use `json.dump()` with `indent=2` for readability
- **CSV**: Use `pd.json_normalize()` then `to_csv()` for flat structure
- **Multiple outputs**: Save both in same script (see `getClientInformation.py` main block)

## External Dependencies & Configuration

### Environment Variables
- `.env` file auto-loaded by `dotenv` in `integrations/qualer_sdk/client.py`
- Key vars: `QUALER_USERNAME`, `QUALER_PASSWORD`, `QUALER_API_KEY`
- Database: `postgresql://postgres:postgres@192.168.1.177:5432/qualer` (hardcoded in `my_qualer_utils.py`, consider parameterizing)

### Key Libraries
- **Selenium**: Browser automation for login
- **BeautifulSoup (bs4)**: HTML parsing
- **requests**: HTTP client (wrapped in authenticated session)
- **pandas**: Data normalization and CSV export
- **tqdm**: Progress bars for bulk operations
- **SQLAlchemy**: Database queries (see `QualerAPIFetcher.run_sql()`)

## File Organization

```
getClientInformation.py         # Example: fetch all clients
getServiceGroups.py            # Example: fetch service groups
getUncertaintyModal.py         # Example: fetch uncertainty modals
my_qualer_utils.py             # Core: QualerAPIFetcher class
integrations/qualer_sdk/       # SDK client configuration
tests/                         # Unit tests
clients.json                   # Input: list of clients to fetch
client_data.json               # Output: extracted client data
client_data.csv                # Output: CSV export
```

## Common Pitfalls & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| 403 Forbidden errors | Expired cookies or insufficient permissions | Wrap in try/except, skip on 403 |
| Script hangs during login | Selenium waiting for page load | Increase `sleep(5)` in `_login()` |
| Empty client data | Form ID changed or parse selector wrong | Print `response.text[:500]` to debug |
| Re-authenticating per request | Calling `get_client_information_with_auth()` in loop | Reuse single `QualerAPIFetcher` + pass `session` |
| Credentials hardcoded | Lazy credential loading | Use `getpass()` prompt or `.env` + `load_dotenv()` |

## When Adding New Extraction Scripts

1. Create `get<Entity>.py` following `getClientInformation.py` pattern
2. Implement `get_<entity>(client_id, session)` function
3. Add bulk processing in `__main__` using `QualerAPIFetcher` context manager
4. Parse HTML with BeautifulSoup (extract form ID, input fields)
5. Output JSON + CSV for each entity
6. Add unit tests in `tests/test_get<Entity>.py` mocking HTTP calls
