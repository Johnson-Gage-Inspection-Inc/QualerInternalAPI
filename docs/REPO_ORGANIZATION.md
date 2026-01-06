# Repository Organization Strategy

## Current Structure (Working, but Not Yet Scalable)
```
QualerInternalAPI/
├── getClientInformation.py
├── getServiceGroups.py
├── getUncertaintyModal.py
├── getUncertaintyParameters.py
├── my_qualer_utils.py              # Core auth utilities
└── integrations/qualer_sdk/        # External SDK client
```

## Proposed Structure (Scaling Towards Internal API SDK)

```
QualerInternalAPI/
├── templates/
│   ├── extraction_template.py      # Template for new scripts
│   └── WORKFLOW.md                 # Step-by-step guide
├── scripts/                        # Actual extraction scripts
│   ├── get_client_information.py
│   ├── get_service_groups.py
│   ├── get_uncertainty_modal.py
│   └── get_uncertainty_parameters.py
├── qualer_internal_sdk/            # Building towards SDK (NEW)
│   ├── __init__.py
│   ├── client.py                   # Internal API client (future)
│   ├── endpoints/
│   │   ├── __init__.py
│   │   ├── client_information.py   # Reusable client_information extraction
│   │   ├── service_groups.py
│   │   └── uncertainty.py
│   └── models.py                   # Response models (dataclasses/pydantic)
├── utils/
│   ├── __init__.py
│   ├── auth.py                     # QualerAPIFetcher (move from root)
│   ├── html_parser.py              # BeautifulSoup utilities
│   └── output.py                   # JSON/CSV export utilities
├── tests/
│   ├── test_scripts/
│   ├── test_sdk/
│   └── fixtures/                   # Mock HTML responses
├── data/
│   ├── clients.json                # Input files
│   ├── client_data.json            # Output files
│   └── client_data.csv
├── docs/
│   ├── API_MAPPING.md              # Map internal endpoints to Qualer UI
│   └── WORKFLOW.md                 # How to add new extractors
└── README.md
```

## Migration Plan (Phase 1: Organize without breaking changes)

1. **Create directory structure** without moving files yet
   ```
   mkdir scripts templates qualer_internal_sdk/endpoints utils docs data
   ```

2. **Move files incrementally**
   - `getClientInformation.py` → `scripts/get_client_information.py`
   - Create `utils/auth.py` with `QualerAPIFetcher`
   - Extract common patterns to `utils/html_parser.py`

3. **Create reusable SDK modules**
   ```python
   # qualer_internal_sdk/endpoints/client_information.py
   def extract_client_information(html: str) -> Dict[str, Any]:
       """Reusable parser for client information form"""
       form = BeautifulSoup(html, "html.parser").find("form", {"id": "ClientInformation"})
       # ... parsing logic
   ```

4. **Update scripts to use SDK**
   ```python
   from qualer_internal_sdk.endpoints.client_information import extract_client_information
   from utils.auth import QualerAPIFetcher
   ```

## Benefits of This Structure

| Aspect | Current | Proposed |
|--------|---------|----------|
| **Adding new endpoint** | Copy getClientInformation.py, customize | Use template + endpoints/ module |
| **Code reuse** | Duplicate parsing logic | Shared `extract_*` functions in endpoints/ |
| **Testing** | Test full scripts | Test individual endpoints + mock HTML |
| **Documentation** | Scattered in docstrings | Central API_MAPPING.md + WORKFLOW.md |
| **SDK development** | Not started | Foundation laid in qualer_internal_sdk/ |
| **Data files** | Scattered in root | Organized in data/ |

## Implementation Order

1. ✅ Create template (`templates/extraction_template.py`)
2. Create directory structure
3. Move existing scripts to `scripts/`
4. Extract `QualerAPIFetcher` to `utils/auth.py`
5. Create `qualer_internal_sdk/endpoints/` modules for reusable parsing
6. Create `docs/API_MAPPING.md` to track endpoints
7. Update `tests/` with endpoint-specific tests
8. Eventually: Unified `qualer_internal_sdk.client()` for easier usage

## When to Do This

**Phase 1 (NOW)**: Create template + structure (no breaking changes)
**Phase 2 (AFTER 3-5 new endpoints)**: Extract to `qualer_internal_sdk/`
**Phase 3 (1-2 months)**: Consolidate into unified SDK client

This preserves all working code while creating a path towards a proper internal API SDK.
