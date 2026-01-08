# Qualer API Endpoint Authentication Patterns

## Overview

Qualer's API endpoints require **browser-like request headers** for authentication beyond just cookies and CSRF tokens. All endpoints can use standard HTTP requests when proper browser fingerprinting headers are included.

---

## Authentication Requirements

**Required Components**:
1. **Authenticated cookies** - From Selenium login session
2. **CSRF token** - ASP.NET double-submit pattern (cookie + form field)
3. **Browser headers** - User-agent, origin, sec-ch-ua family, clientrequesttime

**Methods to use**:
- `api.session.get()` / `api.session.post()` - Direct HTTP with `api.get_headers()`
- `api.get()` - HTTP GET with standard headers
- `api.post()` - HTTP POST with standard headers  
- `api.fetch()` - HTTP GET with `<pre>` tag JSON extraction
- `api.fetch_via_browser()` - Fallback for debugging (slower)

**Characteristics**:
- Standard REST API behavior with browser-like headers
- Fast and efficient (no JavaScript execution needed)
- Validates request origin via headers (not just cookies)

### Known Endpoints

| Endpoint | Path | Method | Pattern | Notes |
|----------|------|--------|---------|-------|
| **Client Information** | `/Client/ClientInformation?clientId={id}` | GET | `fetch_and_store()` | Returns HTML form in `<pre>` tag |
| **Uncertainty Parameters** | `/work/Uncertainties/UncertaintyParameters` | GET | `session.get()` | Direct JSON response |
| **Uncertainty Modal** | `/work/Uncertainties/UncertaintyModal` | GET | `session.get()` | Direct JSON response |
| **Service Groups** | `/work/TaskDetails/GetServiceGroupsForExistingLevels` | GET | `session.get()` | Direct JSON response |
| **Clients Read** | `/ClientDashboard/Clients_Read` | POST | `clients_read()` | Kendo grid data, requires full headers |
| **Clients Count** | `/ClientDashboard/ClientsCountView` | GET | Browser required | May work with headers (untested) |

**Implementation Example**:
```python
# Using session with proper headers
headers = api.get_headers(referer="https://jgiquality.qualer.com/clients")
response = api.session.post(url, data=payload, headers=headers)
data = response.json()

# Or using helper with <pre> tag extraction
api.fetch_and_store(url, "UncertaintyParameters")
```

---

## Critical Headers (From HAR Analysis)

The following headers are **required** for POST requests to pass server-side validation:

```python
{
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache, must-revalidate",
    "clientrequesttime": "2026-01-08T19:35:16",  # UTC timestamp
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://jgiquality.qualer.com",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://jgiquality.qualer.com/clients",  # Context-specific
    "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand\";v=\"24\"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
    "x-requested-with": "XMLHttpRequest",
}
```

**Key discoveries**:
- `clientrequesttime` - Must be current UTC timestamp (validated server-side)
- `origin` - Must match Qualer domain
- `sec-ch-ua` family - Browser client hints (fingerprinting)
- `user-agent` - Full Chrome user agent string
- Missing any of these → 401 Unauthorized

---

## Browser-Based Fallback (Debugging Only) ⚠️

**When to use**: Only if HTTP POST unexpectedly fails or for debugging new endpoints

**Method**: `api.fetch_via_browser()` - Injects JavaScript fetch into browser

**Characteristics**:
- Slower (requires page navigation + JavaScript execution)
- Guaranteed to work (uses actual browser context)
- Useful for debugging when HTTP fails
- Can capture HAR files to analyze missing headers

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
        "__RequestVerificationToken": csrf_token,
    }
)
```

---

## How We Discovered This

The breakthrough came from analyzing a Chrome DevTools HAR export:

1. **Captured working request** - Used Chrome DevTools Network tab, exported HAR
2. **Compared headers** - Identified missing headers in Python `requests` library
3. **Added browser headers** - Updated `get_headers()` to match browser exactly
4. **Result**: HTTP POST changed from 401 → 200 ✅

**Key insight**: Qualer validates request origin beyond cookies/CSRF through browser fingerprinting headers (`sec-ch-ua`, `user-agent`, `clientrequesttime`, `origin`).

---

## Decision Flow: Which Pattern to Use?

```
Is this a POST request to ClientDashboard or similar internal API?
├─ Yes → Try HTTP POST with api.get_headers() first
│   ├─ Success (200) → Fast path, continue using HTTP
│   └─ Fail (401) → Fall back to api.fetch_via_browser()
│
└─ No (standard GET endpoint) → Use direct HTTP
    └─ api.session.get() or api.fetch()
```

**General Rule**: Always try HTTP-first with proper headers. The browser-based method is now a **debugging tool**, not a primary authentication pattern.

---
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
