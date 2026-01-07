# Storage Adapters

QualerInternalAPI uses a pluggable storage adapter pattern to support multiple backends for persisting API responses. This design decouples authentication from persistence, enabling flexible data handling strategies.

## Architecture

```
┌─────────────────────┐
│ QualerAPIFetcher    │  (Auth + HTTP)
└──────────┬──────────┘
           │
           ├──> StorageAdapter (ABC)
           │       ├─> PostgresRawStorage
           │       ├─> CSVStorage  
           │       └─> ORMStorage ✅
           │
           └──> fetch_and_store(url, service)
```

All responses are serialized to JSON before storage, ensuring consistency across backends.

---

## StorageAdapter (Abstract Base Class)

```python
class StorageAdapter(ABC):
    """Abstract interface for storing API responses."""
    
    @abstractmethod
    def store_response(
        self,
        url: str,
        service: str,
        method: str,
        request_headers: Dict[str, Any],
        response_body: str,
        response_headers: Dict[str, Any],
    ) -> None:
        """Store a raw API response."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Clean up resources."""
        pass
```

---

## PostgresRawStorage

**Purpose:** Persistent, queryable database storage with idempotent inserts.

**Schema:**
```sql
CREATE TABLE datadump (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    service TEXT NOT NULL,
    method TEXT NOT NULL,
    request_header JSONB,           -- Serialized request headers
    response_body TEXT,             -- Raw response content
    response_header JSONB,          -- Serialized response headers
    parsed BOOLEAN DEFAULT FALSE,   -- Flag for downstream processing
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(url, service, method)    -- Prevents duplicate inserts
);
```

**Usage:**
```python
from persistence import PostgresRawStorage

# Initialize with database URL
storage = PostgresRawStorage("postgresql://user:pass@localhost:5432/qualer")

# Store responses automatically via QualerAPIFetcher
with QualerAPIFetcher(storage=storage) as api:
    api.fetch_and_store("https://api.example.com/data", "Service")

# Query stored data
results = storage.run_sql("SELECT * FROM datadump WHERE service = :service", 
                          {"service": "Service"})

# Cleanup
storage.close()
```

**Key Features:**
- ✅ ON CONFLICT handling (idempotent - safe to call multiple times)
- ✅ JSONB columns for efficient header queries
- ✅ Backward compatible with existing `run_sql()` interface
- ✅ Automatic JSON serialization of headers

**Thread Safety:** Safe for concurrent reads; exclusive lock during writes (normal PostgreSQL behavior).

---

## CSVStorage

**Purpose:** Lightweight, ad-hoc data export for analysis without database overhead.

**Output Format:**
Creates one CSV file per service in `data/responses/`:
```
timestamp,url,method,response_body,request_headers,response_headers
2026-01-07T13:26:35.882994,https://example.com/api,GET,"{...}","{...}","{...}"
```

**Usage:**
```python
from persistence import CSVStorage

# Initialize with output directory
storage = CSVStorage("data/responses")

# Store responses via QualerAPIFetcher
with QualerAPIFetcher(storage=storage) as api:
    api.fetch_and_store("https://api.example.com/data", "ClientInfo")

# Result: data/responses/ClientInfo.csv
```

**Key Features:**
- ✅ QUOTE_ALL mode prevents CSV injection attacks
- ✅ Auto-creates output directory
- ✅ Appends to existing files
- ✅ No external dependencies (built-in csv module)

**⚠️ Thread Safety:** NOT thread-safe. Multiple threads writing to the same CSV simultaneously can cause:
- Duplicate headers
- Corrupted data
- File locking issues

**Recommendation:** Use CSVStorage for single-threaded scripts only. For concurrent access, use PostgresRawStorage or implement file locking.

---

## ORMStorage

**Purpose:** Type-safe ORM-based storage with SQLAlchemy declarative models and Alembic migration support.

**Status:** ✅ IMPLEMENTED

**Design:**
- Uses SQLAlchemy declarative models for type safety
- Automatic table creation via `Base.metadata.create_all()`
- Graceful duplicate handling (ON CONFLICT via database constraints)
- Full relationship mapping support (future enhancement)
- JSONB columns preserve complex data structures

**Data Model (in `persistence/models.py`):**
```python
class APIResponse(Base):
    """ORM model for raw API responses."""
    __tablename__ = "datadump"
    
    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False)
    service = Column(String, nullable=False)
    method = Column(String, nullable=False)
    request_header = Column(JSONB)          # Stored as JSONB
    response_body = Column(Text)
    response_header = Column(JSONB)         # Stored as JSONB
    parsed = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {...}
```

**Usage Example:**
```python
from persistence.storage import ORMStorage
from persistence.models import APIResponse
from sqlalchemy import select

# Initialize with automatic table creation
storage = ORMStorage("postgresql://user:pass@localhost/qualer")

# Store responses (automatic ON CONFLICT handling)
storage.store_response(
    url="https://api.example.com/clients",
    service="client_information",
    method="GET",
    request_headers={"User-Agent": "python"},
    response_body='{"id": 1, "name": "Client A"}',
    response_headers={"Content-Type": "application/json"}
)

# Query with ORM (type-safe)
session = storage.Session()
responses = session.query(APIResponse).filter(
    APIResponse.service == "client_information",
    APIResponse.parsed == False
).all()

for resp in responses:
    print(f"URL: {resp.url}, Status: {resp.parsed}")
    data_dict = resp.to_dict()  # Convert to dict
    # ... process response ...

session.close()
storage.close()
```

**Key Features:**
- ✅ Type hints for all columns
- ✅ Automatic JSONB serialization/deserialization
- ✅ `to_dict()` method for JSON-safe export
- ✅ Duplicate handling via unique constraint
- ✅ Server-side timestamp (database-managed)
- ✅ No external migration tool required for basic usage

**Thread Safety:** Not thread-safe for concurrent writes. Use session pooling or create separate `ORMStorage` instances for concurrent access.

---

## Using Storage Adapters with QualerAPIFetcher

### Example 1: PostgreSQL (Recommended for production)
```python
from utils.auth import QualerAPIFetcher
from persistence import PostgresRawStorage

storage = PostgresRawStorage("postgresql://localhost/qualer")

with QualerAPIFetcher(storage=storage) as api:
    api.fetch_and_store("https://api.example.com/clients", "ClientDashboard")
    
# Later, query the stored data
results = storage.run_sql("SELECT * FROM datadump LIMIT 10")
storage.close()
```

### Example 2: CSV (Quick analysis)
```python
from utils.auth import QualerAPIFetcher
from persistence import CSVStorage

storage = CSVStorage("./exports")

with QualerAPIFetcher(storage=storage) as api:
    for client_id in [1, 2, 3]:
        api.fetch_and_store(f"https://api.example.com/clients/{client_id}", "ClientInfo")

# Files created: ./exports/ClientInfo.csv
storage.close()
```

### Example 3: Database URL (Backward compatible)
```python
# Old behavior - automatically creates PostgresRawStorage
with QualerAPIFetcher(db_url="postgresql://localhost/qualer") as api:
    api.fetch_and_store("https://api.example.com/clients", "ClientDashboard")
```

### Example 4: No Storage (Auth-only)
```python
# Pure API client - no persistence
with QualerAPIFetcher() as api:
    response = api.session.get("https://api.example.com/data")
    print(response.json())
```

---

## Implementation Pattern

When implementing a new storage adapter:

1. **Inherit from StorageAdapter:**
```python
class MyStorage(StorageAdapter):
    def __init__(self, config):
        self.config = config
    
    def store_response(self, url, service, method, request_headers, response_body, response_headers):
        # Convert dicts to JSON strings
        req_json = json.dumps(request_headers) if isinstance(request_headers, dict) else request_headers
        res_json = json.dumps(response_headers) if isinstance(response_headers, dict) else response_headers
        
        # Implement storage logic
        ...
    
    def close(self):
        # Cleanup resources
        pass
```

2. **Handle Header Serialization:**
Headers come in as dicts but may be JSON strings on subsequent calls. Always check:
```python
req_json = json.dumps(req_headers) if isinstance(req_headers, dict) else req_headers
```

3. **Add Tests:**
```python
def test_my_storage(tmpdir):
    storage = MyStorage(tmpdir)
    storage.store_response(
        url="https://example.com",
        service="Test",
        method="GET",
        request_headers={"key": "value"},
        response_body="response",
        response_headers={"header": "value"}
    )
    # Verify storage worked
    storage.close()
```

---

## Performance Considerations

| Adapter | Throughput | Latency | Concurrency | Best For |
|---------|-----------|---------|-------------|----------|
| PostgresRawStorage | 1000s/sec | ~10ms | ✅ Excellent | Production, concurrent loads |
| CSVStorage | 100s/sec | ~5ms | ❌ Poor | Ad-hoc analysis, small datasets |
| ORMStorage | 100s/sec | ~20ms | ✅ Good | Complex queries, relationships |

**Optimization Tips:**
- Use batch inserts for bulk operations (>1000 records)
- Connection pooling (SQLAlchemy enables automatically)
- CSV: Use separate files per thread to avoid locking
- PostgreSQL: Index on `(service, created_at)` for time-range queries

---

## Troubleshooting

**Problem:** "Storage engine not initialized"
- **Cause:** Called `fetch_and_store()` without storage configured
- **Fix:** Pass `storage=` or `db_url=` to QualerAPIFetcher

**Problem:** CSV injection warnings
- **Cause:** Using unsafe quoting mode in CSV
- **Fix:** CSVStorage already uses `QUOTE_ALL` - no manual quoting needed

**Problem:** "can't adapt type 'dict'" in PostgreSQL
- **Cause:** Headers not serialized to JSON
- **Fix:** storage.py automatically serializes with `json.dumps()` - should be fixed

**Problem:** CSV file has duplicate headers
- **Cause:** Multiple threads writing simultaneously
- **Fix:** Use CSVStorage only in single-threaded context, or implement file locking

---

## See Also

- [Database Schema Documentation](DATABASE_SCHEMA.md)
- [QualerAPIFetcher Usage](../README.md)
- [tests/test_storage.py](../tests/test_storage.py) - Unit test examples
