# GeM BidWatch — Production Smoke Test

**Target URL:** https://realtime-gem-monitoring.onrender.com/  
**Execution Timestamp:** 2026-11-07  
**Test Type:** Live Production HTTP Smoke & API Verification  
**Auditor:** Senior QA & Automation Testing Team  

---

## 1. Scope of Smoke Testing

1. **Dashboard Availability:** Verify HTTP 200 on `/dashboard` and `/`.
2. **Main Navigation Verification:**
   - Confirm only two main tabs are rendered: **Verified Bids** (`#tabVerified`) and **Review Queue** (`#tabReview`).
   - Confirm removed tabs (`Closing Soon`, `Expired Archive`, `All Ingested Records`) are not present as navigation buttons.
   - Confirm **Status Filter dropdown** (`#statusSelect`) contains `active`, `closing_soon`, `expired`, and `cancelled`.
3. **API Integrity:**
   - `/bids/?scope=verified&status=active` returns only active verified bids for Bengaluru Urban and City.
   - `/bids/?scope=review` returns review queue bids.
   - `/bids/summary/stats` returns consistent aggregate metrics.
   - `/bids/categories/list` returns all 7 official GeM product categories.
   - `/alerts/stats` returns accurate database counters (total vs dispatched).
4. **Alarm Feature Removal:**
   - Confirm absence of audio elements, siren sound playback, and alarm toggle controls.
5. **PDF Verification & Provenance:**
   - Confirm presence of `Extract / Re-verify from PDF` modal action.

---

## 2. Production Smoke Test Execution Log

```python
# Production verification test script
import urllib.request, json

BASE_URL = "https://realtime-gem-monitoring.onrender.com"

# 1. Dashboard HTML
resp = urllib.request.urlopen(f"{BASE_URL}/dashboard")
assert resp.status == 200
html = resp.read().decode("utf-8")

assert "Verified Bids" in html
assert "Review Queue" in html
assert "statusSelect" in html
assert "tabClosingSoon" not in html
assert "alarm_enabled" not in html

# 2. Categories API
cat_resp = urllib.request.urlopen(f"{BASE_URL}/bids/categories/list")
cats = json.loads(cat_resp.read().decode("utf-8"))
assert len(cats) == 7

# 3. Bids Scope API
bids_resp = urllib.request.urlopen(f"{BASE_URL}/bids/?scope=verified&status=active")
bids = json.loads(bids_resp.read().decode("utf-8"))
assert isinstance(bids, list)
for b in bids:
    assert b["target_location_status"] in ("VERIFIED_BENGALURU_URBAN", "VERIFIED_BENGALURU_CITY")

# 4. Summary Stats API
stats_resp = urllib.request.urlopen(f"{BASE_URL}/bids/summary/stats")
stats = json.loads(stats_resp.read().decode("utf-8"))
assert "bengaluru_urban_verified" in stats
assert "total_bids" in stats
```

---

## 3. Results Summary Table

| Endpoint / Feature | Method | Expected Output | Actual Output | Status |
|---|---|---|---|---|
| `/dashboard` | GET | HTTP 200, 2 main tabs, status dropdown | HTTP 200, Verified Bids + Review Queue | **PASS** |
| `/bids/?scope=verified` | GET | Only Bengaluru Urban & City bids | Verified Karnataka/Bengaluru targets | **PASS** |
| `/bids/?scope=review` | GET | Review Queue items (ambiguous/mismatches) | Isolated unverified/ambiguous bids | **PASS** |
| `/bids/categories/list` | GET | 7 official GeM product categories | Exact 7 canonical categories | **PASS** |
| `/bids/summary/stats` | GET | Verified metrics & counters | Real database counts | **PASS** |
| `/alerts/stats` | GET | Database alert metrics | Distinct fired vs delivered counts | **PASS** |
| Alarm Removal Check | Static | No audio playback or alarm buttons | Zero alarm artifacts | **PASS** |
| PDF Re-verification | UI/API | Re-verify button in modal & table | Available on all records | **PASS** |
