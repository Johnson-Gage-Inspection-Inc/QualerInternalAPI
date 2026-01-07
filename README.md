# QualerInternalAPI

A Python SDK for reverse-engineering and accessing Qualer's internal API. Automatically handles authentication, parses HTML responses, and provides a clean interface for data extraction.

## Quick Start

```python
from qualer_internal_sdk import QualerClient

with QualerClient() as client:
    # Fetch all clients
    clients = client.client_dashboard.clients_read()
    # API returns "Data" (capital D) in the response
    print(f"Found {len(clients.get('Data', []))} clients")

    # Fetch client information
    client_ids = [c["Id"] for c in clients["Data"]]
    client.client.fetch_and_store(client_ids)
```

## Installation

```bash
# Clone and install in development mode
git clone https://github.com/Johnson-Gage-Inspection-Inc/QualerInternalAPI.git
cd QualerInternalAPI
pip install -e .
pip install -r requirements.txt
```

## Configuration

Set environment variables in `.env`:

```bash
# Database
DB_URL=postgresql://user:pass@host:5432/qualer

# Qualer Credentials
QUALER_USERNAME=user@example.com
QUALER_PASSWORD=secret_password

# Performance Tuning (optional)
QUALER_LOGIN_WAIT_TIME=5.0          # Seconds to wait after login
QUALER_REQUEST_TIMEOUT=30.0         # Request timeout in seconds
```

If env vars not set, you'll be prompted for credentials interactively.

## Usage Patterns

### Pattern 1: Simple Data Fetch

```python
from qualer_internal_sdk import QualerClient

with QualerClient() as client:
    clients = client.client_dashboard.clients_read()
    for c in clients["Data"]:
        print(c["Name"])
```

### Pattern 2: Full Data Pipeline

```python
with QualerClient() as client:
    # Fetch all clients
    clients_resp = client.client_dashboard.clients_read()
    client_ids = [c["Id"] for c in clients_resp["Data"]]
    
    # Fetch detailed information
    client.client.fetch_and_store(client_ids)
    
    # Parse and export (separate scripts)
    # python scripts/parseClientInformation.py
```

### Pattern 3: Debugging (Non-Headless)

```python
# Watch the browser during execution
with QualerClient(headless=False) as client:
    result = client.client_dashboard.clients_read()
```

### Pattern 4: Slow Network

```python
# Increase wait time if login times out
with QualerClient(login_wait_time=15.0) as client:
    pass
```

## Scripts

### `scripts/Clients_Read.py`

Fetch and save all clients to `data/clients.json`:

```bash
python scripts/Clients_Read.py
```

### `scripts/getClientInformation.py`

Fetch and store detailed client information in database:

```bash
python scripts/getClientInformation.py
```

### `scripts/parseClientInformation.py`

Parse stored HTML and export as JSON/CSV:

```bash
python scripts/parseClientInformation.py
```

### `scripts/getServiceGroups.py`

Fetch and store service groups for all work items:

```bash
python scripts/getServiceGroups.py
```

### `scripts/getUncertaintyParameters.py`

Fetch and store uncertainty parameters for all measurements:

```bash
python scripts/getUncertaintyParameters.py
```

### `scripts/getUncertaintyModal.py`

Fetch and store uncertainty modals for all measurement batches:

```bash
python scripts/getUncertaintyModal.py
```

## Architecture

### Unified Client Interface

The `QualerClient` provides a clean, nested API:

```python
with QualerClient() as client:
    client.client_dashboard.clients_read()      # Fetch all clients
    client.client.fetch_and_store(ids)          # Fetch client details
    client.service.get_service_groups(item_id)  # Fetch service groups
    client.uncertainty.get_parameters(m_id, b_id)  # Fetch uncertainty parameters
    client.uncertainty.get_modal(m_id, b_id)    # Fetch uncertainty modal
```

### Endpoint Modules

Organized by URL structure and functionality:

```
qualer_internal_sdk/endpoints/
  ├── client_dashboard/
  │   └── clients_read.py          # POST /ClientDashboard/Clients_Read
  ├── client/
  │   └── client_information.py    # GET /Client/ClientInformation
  ├── service/
  │   └── service_groups.py        # GET /work/TaskDetails/GetServiceGroupsForExistingLevels
  └── uncertainty/
      ├── uncertainty_parameters.py # GET /work/Uncertainties/UncertaintyParameters
      └── uncertainty_modal.py      # GET /work/Uncertainties/UncertaintyModal
```

### Core Infrastructure

- **`utils/auth.py`** - Selenium-based authentication, session management, database access
- **`utils/html_parser.py`** - HTML form field extraction utilities
- **`qualer_internal_sdk/client.py`** - Unified client interface (context manager)

## Key Features

✅ **Unified Interface** - Single entry point with nested namespaces  
✅ **Automatic Auth** - Context manager handles login/cleanup  
✅ **Database Storage** - Fetch responses automatically stored in PostgreSQL  
✅ **HTML Parsing** - Extract structured data from HTML forms  
✅ **Content-Type Aware** - Handles both JSON and HTML responses  
✅ **Flexible Config** - Environment variables or interactive prompts  
✅ **Debugging Support** - Disable headless mode to watch browser  

## Project Structure

```
c:\Users\JeffHall\git\QualerInternalAPI\
├── README.md                    # This file
├── qualer_internal_sdk/
│   ├── __init__.py
│   ├── client.py                # Unified QualerClient
│   └── endpoints/
│       ├── client_dashboard/
│       ├── client/
│       ├── service/
│       └── uncertainty/
├── scripts/
│   ├── Clients_Read.py
│   ├── getClientInformation.py
│   ├── parseClientInformation.py
│   └── ...
├── examples/
│   └── unified_client_example.py
├── utils/
│   ├── auth.py
│   └── html_parser.py
├── tests/
├── docs/
└── pyproject.toml
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
flake8 .              # Linting (ignores line length per .flake8)
mypy .                # Type checking
isort --check-only .  # Import sorting
```

### Adding New Endpoints

1. Create module in `qualer_internal_sdk/endpoints/<path>/`
2. Implement extraction logic (fetch, parse, return dict)
3. Export from `__init__.py`
4. Add method to corresponding `*Endpoint` class in `qualer_internal_sdk/client.py`
5. Use in scripts: `client.<namespace>.<endpoint>()`

## How It Works

### Authentication Flow

1. **Selenium Login** - Automates browser login to Qualer
2. **Cookie Extraction** - Copies authenticated cookies from Selenium to requests Session
3. **Session Reuse** - Uses authenticated Session for subsequent API calls
4. **Auto Cleanup** - Closes Selenium driver on context exit

### Data Extraction Pattern

1. **Fetch** - Make authenticated HTTP request, store in database
2. **Parse** - Extract structured data from HTML/JSON response
3. **Export** - Convert to JSON/CSV for downstream use

### Database Storage

Responses automatically stored in `datadump` table with:
- `url` - Endpoint URL
- `service` - Service name (e.g., "client_dashboard")
- `method` - HTTP method (GET/POST)
- `request_header` - Request headers (JSON)
- `response_body` - Response body (raw)
- `response_header` - Response headers (JSON)
- `parsed` - Flag indicating if parsed

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| 403 Forbidden | Permission denied or expired session | Wrap in try/except, skip on 403 |
| Script hangs | Selenium waiting for page | Increase `login_wait_time` |
| No data returned | Form selector wrong or page layout changed | Debug with `headless=False` |
| Import errors | Package not installed in editable mode | Run `pip install -e .` |
| Database errors | Connection string wrong | Check `DB_URL` env var |

## Environment

- **Python**: 3.10+
- **Database**: PostgreSQL 12+
- **Browser**: Chrome/Chromium (automated via Selenium)

### Dependencies

See `requirements.txt`:
- `selenium` - Browser automation
- `beautifulsoup4` - HTML parsing
- `requests` - HTTP client
- `pandas` - Data manipulation
- `sqlalchemy` - Database ORM
- `psycopg2-binary` - PostgreSQL driver
- `python-dotenv` - Environment variables
- `tqdm` - Progress bars

## License

Internal use only - Johnson Gage Inspection Inc

## Contributing

When updating the SDK:
1. Update this README with new features/patterns
2. Don't create separate phase documentation
3. Keep examples simple and practical
4. Maintain backward compatibility when possible
