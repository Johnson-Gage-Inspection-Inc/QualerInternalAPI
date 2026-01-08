# Copilot Instructions for QualerInternalAPI

## Project Overview
QualerInternalAPI is a Python-based data extraction pipeline for the Qualer quality management system. It fetches client and service data from the Qualer web application, parses HTML responses, and stores results in multiple formats (JSON, CSV, PostgreSQL).

## Architecture & Key Components

### Core Authentication Pattern
**Pattern**: `QualerAPIFetcher` (context manager in `utils/auth.py`)
- Handles browser automation via Selenium for Qualer login
- Automatically extracts authenticated cookies into a `requests.Session`
- Provides both DB access (SQLAlchemy) and HTTP/browser-based API access
- **Always use as context manager**: `with QualerAPIFetcher() as fetcher: ...`
- Credentials: `QUALER_EMAIL`/`QUALER_PASSWORD`/`DB_URL` env vars or interactive prompt
- Cleans up Selenium driver automatically on exit

**API Access Pattern** (see `docs/ENDPOINT_AUTHENTICATION_PATTERNS.md` and `docs/BREAKTHROUGH_HTTP_AUTHENTICATION.md`):
- **HTTP-First** (`api.get()`, `api.post()`, `api.session.get/post()` with `api.get_headers()`):
  - Standard REST API requests using `requests.Session`
  - **Requires browser fingerprinting headers** (clientrequesttime, origin, sec-ch-ua family, user-agent)
  - Fast and efficient (~10x faster than browser-based)
  - Works for: ALL endpoints including ClientDashboard (Clients_Read, ClientsCountView), Client Information, Uncertainty endpoints, Service Groups
  - **Always use this first** - `api.get_headers()` includes all required browser headers
  
- **Browser-Based Fallback** (`api.fetch_via_browser()`):
  - JavaScript fetch() executed inside authenticated browser
  - **Use only for debugging** when HTTP unexpectedly fails
  - Slower but guaranteed to work (actual browser context)
  - Useful for capturing HAR files to analyze missing headers

**Key Discovery (Jan 2026)**: Qualer validates requests using browser fingerprinting beyond cookies/CSRF. The `get_headers()` method now includes all required headers (`clientrequesttime` timestamp, `origin`, `sec-ch-ua` family, full `user-agent`). Missing these → 401 Unauthorized.

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
# Activate virtual environment (Once per terminal session)
.venv\Scripts\Activate.ps1

# First-time setup: install editable package
pip install -e .
pip install -r requirements.txt
# Run extraction script from any directory (imports work cleanly)
python scripts/getClientInformation.py

# With environment variables pre-set
$env:QUALER_EMAIL="user@jgiquality.com"; python scripts/getClientInformation.py
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
- `.env` file auto-loaded by `dotenv` in `utils/auth.py` and `parse.py`
- Key vars: `QUALER_EMAIL`, `QUALER_PASSWORD`, `QUALER_API_KEY`, `DB_URL`
- Database: Use `DB_URL` environment variable (e.g., `postgresql://postgres:postgres@192.168.1.177:5432/qualer`)

### Key Libraries
- **Selenium**: Browser automation for login
- **BeautifulSoup (bs4)**: HTML parsing
- **requests**: HTTP client (wrapped in authenticated session)
- **pandas**: Data normalization and CSV export
- **tqdm**: Progress bars for bulk operations
- **SQLAlchemy**: Database queries (see `QualerAPIFetcher.run_sql()`)

## File Organization

```
scripts/
  getClientInformation.py       # Example: fetch all clients
  getServiceGroups.py           # Example: fetch service groups
  getUncertaintyModal.py        # Example: fetch uncertainty modals
  getUncertaintyParameters.py   # Example: fetch uncertainty parameters
utils/
  auth.py                       # Core: QualerAPIFetcher class
qualer_internal_sdk/
  endpoints/                    # Reusable endpoint modules (future)
integrations/qualer_sdk/       # SDK client configuration
tests/                         # Unit tests
data/                          # Input/output data files
my_qualer_utils.py             # Backward compatibility shim
parse.py                       # Utility: parse UncertaintyModal responses
parseToolTypes.py              # Utility: parse ToolTypes.json
pyproject.toml                 # Package configuration (editable install)
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

## Workflow for Discovering New Endpoints

This repo is a sandbox for reverse-engineering Qualer's internal API (not documented in their SDK). Use this workflow:

1. **Navigate to Qualer UI** - Find the page with desired data at `https://jgiquality.qualer.com`
2. **Open Chrome DevTools** - Press F12, go to **Network** tab
3. **Capture the request** - Perform the action, find the Fetch/XHR request in Network
4. **Copy the request** - Right-click request → **Copy as** → fetch/cURL/PowerShell
5. **Extract key info**:
   - URL (endpoint + query params)
   - HTTP method (GET/POST/etc)
   - Headers (referer, x-requested-with, etc)
   - Request body (if POST)
   - Response type (JSON vs HTML form)
6. **Use the template** - Copy `templates/extraction_template.py` and fill in the blanks
7. **Update script** - Replace TODO comments with actual endpoint details
8. **Test locally** - Run with `headless=False` to see browser during auth

## Template Usage Example

```bash
# Copy template
cp templates/extraction_template.py scripts/get_new_entity.py

# Edit script:
# - Replace "entity_information" with your endpoint
# - Update form ID (from DevTools HTML response)
# - Update file names (entities.json, entity_data.json)
# - Update data structure path (if JSON response differs)

# Run with authentication
python scripts/get_new_entity.py
```

## Repository Organization Strategy

See `docs/REPO_ORGANIZATION.md` for the plan to scale this towards a unified internal API SDK. Key structure:

- `scripts/` - Individual extraction scripts (use template)
- `qualer_internal_sdk/endpoints/` - Reusable parsing modules (future)
- `utils/` - Shared auth, HTML parsing, output utilities
- `templates/` - Template script and workflow docs
- `docs/API_MAPPING.md` - Track discovered endpoints (TBD)
