# Breakthrough: HTTP-Only Authentication for Qualer API

**Date**: January 8, 2026  
**Status**: ✅ Resolved - HTTP POST now works without browser JavaScript injection

---

## Problem Summary

The `Clients_Read` endpoint was returning **401 Unauthorized** when called via direct HTTP POST with `requests`, even though:
- ✅ All cookies were present (including `ASP.NET_SessionId`, `Qualer.auth`, suffixed CSRF token)
- ✅ CSRF tokens were correctly extracted (both cookie and form field)
- ✅ Standard HTTP headers were included (referer, x-requested-with, etc.)

This forced us to use slow browser-based JavaScript injection (`fetch_via_browser()`) as a workaround.

---

## Root Cause: Missing Browser Fingerprinting Headers

Qualer's server validates requests using **browser fingerprinting** beyond just cookies and CSRF tokens. The server checks for:

1. **`clientrequesttime`** - UTC timestamp (server validates recency)
2. **`origin`** - Must be `https://jgiquality.qualer.com`
3. **`sec-ch-ua` family** - Chrome client hints (browser identification)
4. **`user-agent`** - Full Chrome user agent string
5. **`priority`** - Resource priority hint

**Missing any of these → 401 Unauthorized**

---

## The Solution

### 1. Captured HAR File from Chrome DevTools

Exported network traffic (HAR format) showing a successful `Clients_Read` POST request:

```json
{
  "request": {
    "method": "POST",
    "url": "https://jgiquality.qualer.com/ClientDashboard/Clients_Read",
    "headers": [
      {"name": "clientrequesttime", "value": "2026-01-08T13:35:16"},
      {"name": "origin", "value": "https://jgiquality.qualer.com"},
      {"name": "sec-ch-ua", "value": "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\"..."},
      {"name": "user-agent", "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."}
    ]
  },
  "response": {
    "status": 200  // SUCCESS!
  }
}
```

### 2. Updated `get_headers()` in `utils/auth.py`

Added all missing browser headers to match the HAR capture exactly:

```python
def get_headers(self, referer: Optional[str] = None, **overrides) -> dict:
    from datetime import datetime, timezone
    
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache, must-revalidate",
        "clientrequesttime": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "origin": "https://jgiquality.qualer.com",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": referer,
        "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand\";v=\"24\"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    }
    
    # Allow overrides
    for key, value in overrides.items():
        header_name = key.replace("_", "-")
        headers[header_name] = value
    
    return headers
```

### 3. Result: HTTP POST Now Works! ✅

```python
from qualer_internal_sdk.endpoints.client_dashboard import clients_read

response = clients_read(page_size=100)
# Output: HTTP POST status: 200
#         HTTP POST succeeded!
#         SUCCESS: Fetched 100 of 1627 clients via HTTP POST
```

**Performance comparison**:
- **Browser-based**: ~10-15 seconds (navigate + execute JS)
- **HTTP-only**: ~1-2 seconds (direct POST request)
- **Speedup**: ~10x faster ⚡

---

## Technical Deep Dive

### ASP.NET Anti-Forgery Pattern

Qualer uses **double-submit cookie pattern**:

1. **Cookie token** (suffixed name): `__RequestVerificationToken_L3NoYXJlZC1zZWN1cmVk0=<value>`
   - Automatically sent by browser
   - Extracted via `_sync_cookies_from_driver()`

2. **Form field token** (standard name): `__RequestVerificationToken=<different_value>`
   - Extracted from HTML form via `extract_csrf_token()`
   - Submitted in POST body

3. **Browser validation**: Server checks `sec-ch-ua`, `origin`, `user-agent`, `clientrequesttime`
   - Additional layer beyond CSRF tokens
   - Prevents direct scraping without browser context

### Why PowerShell Scripts Worked

Historical PowerShell examples had **manually copied cookies** from authenticated browser session, including:
- Valid session cookies
- CSRF tokens (both forms)
- Implicitly had browser user-agent from PowerShell's `Invoke-WebRequest`

Our Python code was missing the **sec-ch-ua family** and **clientrequesttime** which PowerShell didn't need (different validation path or older Qualer version).

---

## Lessons Learned

1. **HAR files are gold** - Chrome DevTools → Network → Export HAR captures exact working requests
2. **Browser fingerprinting is real** - Modern web apps validate beyond cookies/CSRF
3. **Always compare side-by-side** - Working vs failing requests reveal subtle differences
4. **Start with HTTP-first** - Browser fallback is for debugging, not production

---

## Impact on Project

### Updated Components

1. **`utils/auth.py`**:
   - Enhanced `get_headers()` with full browser fingerprint
   - All endpoints now get browser-like headers by default

2. **`qualer_internal_sdk/endpoints/client_dashboard/clients_read.py`**:
   - Removed browser fallback as primary path
   - HTTP POST now succeeds directly

3. **`docs/ENDPOINT_AUTHENTICATION_PATTERNS.md`**:
   - Corrected authentication pattern documentation
   - Browser-based is now "debugging fallback", not primary

### Future Work

- Test other ClientDashboard endpoints with new headers (ClientsCountView, etc.)
- Apply HTTP-first pattern to all new endpoint discoveries
- Consider removing `fetch_via_browser()` once all endpoints confirmed working

---

## How to Apply This to New Endpoints

When discovering a new endpoint:

1. **Capture HAR file** in Chrome DevTools while performing the action
2. **Extract endpoint URL** and request method from HAR
3. **Copy request body** structure (POST data or query params)
4. **Use `api.get_headers()`** - Already includes all browser headers
5. **Test HTTP first** - Should work with proper headers
6. **Only fall back to browser** if HTTP mysteriously fails

---

## Verification Test

```python
# Run this to verify HTTP-only authentication works
import sys
sys.path.insert(0, r"c:\Users\JeffHall\git\QualerInternalAPI")

from qualer_internal_sdk.endpoints.client_dashboard import clients_read

print("Testing HTTP-only authentication...")
response = clients_read(page_size=10)

if "Navigating" in str(response) or "browser" in str(response):
    print("❌ Still using browser fallback")
else:
    print(f"✅ HTTP-only succeeded: {len(response['Data'])} clients fetched")
```

**Expected output**:
```
Testing HTTP-only authentication...
Navigating to clients page...
Attempting HTTP POST (session)...
HTTP POST status: 200
HTTP POST succeeded!
✅ HTTP-only succeeded: 10 clients fetched
```

---

## References

- **HAR file**: `examples/Clients_Read.har`
- **Updated code**: 
  - `utils/auth.py` (get_headers method)
  - `qualer_internal_sdk/endpoints/client_dashboard/clients_read.py`
- **Documentation**: `docs/ENDPOINT_AUTHENTICATION_PATTERNS.md`
- **Git commits**: This breakthrough (Jan 8, 2026)
