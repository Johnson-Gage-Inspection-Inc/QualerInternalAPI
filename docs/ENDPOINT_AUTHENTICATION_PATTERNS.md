# Qualer API Endpoint Authentication Patterns

## Overview

Qualer's API has **two different authentication patterns** for different endpoint types. Understanding which pattern an endpoint uses is critical for successful implementation.

---

## Pattern 1: HTTP-Based (Standard REST API) ✅

**Works with**: Direct HTTP requests using `requests.Session`

**Methods to use**:
- `api.session.get()` - Direct HTTP GET
- `api.get()` - HTTP GET with standard headers
- `api.post()` - HTTP POST with standard headers  
- `api.fetch()` - HTTP GET with `<pre>` tag JSON extraction

**Characteristics**:
- Standard REST API behavior
- Accepts authenticated HTTP requests with cookies
- Returns JSON or HTML-wrapped JSON
- Fast and efficient

### Known HTTP-Compatible Endpoints

| Endpoint | Path | Method | Pattern | Notes |
|----------|------|--------|---------|-------|
| **Client Information** | `/Client/ClientInformation?clientId={id}` | GET | `fetch_and_store()` | Returns HTML form in `<pre>` tag |
| **Uncertainty Parameters** | `/work/Uncertainties/UncertaintyParameters` | GET | `session.get()` | Direct JSON response |
| **Uncertainty Modal** | `/work/Uncertainties/UncertaintyModal` | GET | `session.get()` | Direct JSON response |
| **Service Groups** | `/work/TaskDetails/GetServiceGroupsForExistingLevels` | GET | `session.get()` | Direct JSON response |

**Implementation Example**:
```python
# Using direct session
url = "https://jgiquality.qualer.com/work/Uncertainties/UncertaintyParameters"
response = api.session.get(url, params={"measurementId": 123})
data = response.json()

# Or using helper with <pre> tag extraction
api.fetch_and_store(url, "UncertaintyParameters")
```

---

## Pattern 2: Browser-Based (JavaScript Required) ⚠️

**Requires**: JavaScript `fetch()` executed inside authenticated browser context

**Method to use**:
- `api.fetch_via_browser()` - Injects JavaScript fetch into browser

**Characteristics**:
- **Returns 401 with direct HTTP** even with valid cookies/CSRF
- Validates that request originates from JavaScript in browser
- Typically internal/undocumented APIs
- Slower (requires page navigation + JavaScript execution)
- Used for ClientDashboard and similar internal features

### Known Browser-Required Endpoints

| Endpoint | Path | Method | Auth Page | Notes |
|----------|------|--------|-----------|-------|
| **Client Count View** | `/ClientDashboard/ClientsCountView` | GET | `/ClientDashboard/Clients` | Returns client category counts |
| **Clients Read** | `/ClientDashboard/Clients_Read` | POST | `/clients` | Paginated client list with Kendo Grid format |

**Why does this happen?**
- These endpoints likely have additional JavaScript-based validation
- May check for browser context indicators beyond cookies
- Possibly part of anti-scraping or security measures
- Internal APIs not designed for direct HTTP consumption

**Implementation Example**:
```python
response = api.fetch_via_browser(
    method="POST",
    endpoint_path="/ClientDashboard/Clients_Read",
    auth_context_page="/clients",
    params={
        "sort": "ClientCompanyName-asc",
        "page": 1,
        "pageSize": 100,
    }
)
```

---

## How to Determine Which Pattern an Endpoint Uses

### Discovery Process:

1. **Try HTTP first** (it's faster):
   ```python
   response = api.get(url, params={...})
   ```

2. **If you get 401 Unauthorized**:
   - Even with valid cookies
   - Even with CSRF token
   - → Switch to browser-based approach

3. **Use browser-based approach**:
   ```python
   response = api.fetch_via_browser(
       method="GET",  # or "POST"
       endpoint_path="/path/to/endpoint",
       auth_context_page="/related/page",
       params={...}
   )
   ```

### Testing Checklist:

- [ ] Try with `api.session.get()` or `api.get()`
- [ ] Check response status code
- [ ] If 401: Note the endpoint requires browser context
- [ ] Find appropriate auth context page (usually the UI page that uses the endpoint)
- [ ] Implement with `fetch_via_browser()`

---

## Auth Context Pages

For browser-based endpoints, you must navigate to a page that establishes authentication context **before** calling the API. Common patterns:

| Feature Area | Auth Context Page | Endpoints That Need It |
|--------------|-------------------|------------------------|
| Client Dashboard | `/clients` or `/ClientDashboard/Clients` | Clients_Read, ClientsCountView |
| Work/Tasks | `/work/TaskDetails/...` | (Likely for POST operations) |
| Uncertainties | `/work/Uncertainties/...` | (May be needed for POST operations) |

**How to find the auth context page:**
1. Open Chrome DevTools → Network tab
2. Navigate to the Qualer UI feature
3. Perform the action that triggers the API call
4. Look at the **Referer** header in the Network request
5. Use that page as your `auth_context_page`

---

## Performance Considerations

| Pattern | Speed | Use Case |
|---------|-------|----------|
| HTTP-Based | Fast (~100-200ms) | Bulk data fetching, automated jobs |
| Browser-Based | Slow (~3-5s) | Interactive features, internal APIs |

**Optimization Tips**:
- Reuse single `QualerAPIFetcher` context for multiple requests
- For browser-based: Batch requests within same auth context (avoid re-navigating)
- Prefer HTTP-based endpoints when both patterns work

---

## Summary Decision Tree

```
Do you have the endpoint URL?
  │
  ├─→ Try api.get() or api.session.get()
  │     │
  │     ├─→ Works (200 OK)? → Use HTTP pattern ✅
  │     │
  │     └─→ Gets 401? → Use browser pattern ⚠️
  │           │
  │           └─→ Use api.fetch_via_browser()
  │
  └─→ New endpoint discovery?
        │
        └─→ Check Chrome DevTools Network tab
              │
              ├─→ XHR/Fetch request succeeds in browser?
              │     └─→ Use browser pattern
              │
              └─→ Check if direct HTTP works
                    └─→ Use HTTP pattern if possible
```

---

## Future Endpoints

When implementing a new endpoint, **document which pattern it uses** in this file to help future developers.

**Template**:
```markdown
| Endpoint Name | `/path/to/endpoint` | GET/POST | HTTP or Browser | Notes |
```
