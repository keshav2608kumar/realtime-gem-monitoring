# GeM BidWatch — Production System Audit & Root Cause Analysis

**Deployment URL:** https://realtime-gem-monitoring.onrender.com/  
**Repository:** https://github.com/keshav2608kumar/realtime-gem-monitoring.git  
**Version:** Enterprise v2.5  
**Audit Date:** 2026-11-07  
**Test Suite Status:** 56 Tests Passed (0 Failures, 100% Pass Rate)

---

## 1. Executive Summary

A comprehensive architectural and operational audit of the deployed **GeM BidWatch** enterprise procurement application was conducted. The audit traced the end-to-end data pipeline from user interface to the official Government e-Marketplace (GeM) source documents, covering:

`UI (Dashboard)` → `REST APIs (FastAPI)` → `Business Logic & Services` → `Database (SQLite/PostgreSQL)` → `GeM Adapter & Official PDFs` → `Location Normalization` → `Corrigenda Resolution` → `Alert & Siren Dispatch`

All identified defects—including the live public page failure, location shadowing, placeholder address false-negatives, missing corrigendum deadline extensions, and incomplete alert popups—have been completely diagnosed at root cause, repaired, and regression-tested.

---

## 2. Root Cause Analysis of Live Page Failures

### 2.1 "Showing 0 of 0 tenders" & False "OUTSIDE_TARGET" Classification
* **Symptoms:** The live public page showed `Showing 0 of 0 tenders`, summary counters showed `--`, and official test tender `GEM/2026/B/8123875` was missing from the verified feed.
* **Root Cause:**
  When `pdf_location_extractor.py` was invoked on a bid whose PDF was either pending download or failed parsing, it set `full_address` to the diagnostic message `"Delivery address could not be verified from the available document."`.
  When `resolve_effective_bid_delivery_location()` evaluated Priority 1 (`pdf_delivery_address`), `any([pdf_addr, ...])` evaluated to `True`. The extractor then called `classify_bengaluru_urban(raw_text="Delivery address could not be verified...")`.
  Because this error message contains neither "Bangalore" nor an urban PIN code, it fell into rule 8 (`STATUS_OUTSIDE_TARGET`), which short-circuited evaluation before Priority 2 (`delivery_*`) or Priority 3 (`consignee_city: Bangalore Urban, consignee_district: Bangalore Urban`) were ever checked. Valid Bangalore Urban bids were thus systematically classified as `OUTSIDE_TARGET` and excluded from `scope=bengaluru_urban`.
* **Resolution:**
  1. Updated `resolve_effective_bid_delivery_location()` to explicitly detect failure/diagnostic placeholders (`"could not be verified"`, `"unavailable"`, etc.) and treat them as non-geographic strings.
  2. Implemented seamless fallback: If Priority 1 does not yield a verified location, the engine immediately checks Priority 2 (source delivery location) and Priority 3 (consignee administrative location).
  3. Upgraded `parse_consignee_block()` to recognize GeM schedule evaluation tables (e.g. `Evaluation Schedules`, `Schedule 1 ( Bangalore Urban )`, `Location of Consignee: Bangalore Urban`), enabling high-confidence extraction (`confidence=0.90`, `status=VERIFIED`).

### 2.2 "Match Alert Detected with Missing Details (--)"
* **Symptoms:** Red siren modal appeared displaying `--` for tender number, category, department, location, and deadline.
* **Root Cause:**
  In `dashboard.py`, `checkUnacknowledgedAlerts()` fetched the top unacknowledged alert. While `renderActiveBanner()` populated the top sticky banner, the modal elements (`modalTenderNo`, `modalCategory`, `modalDept`, `modalLocation`, `modalEndDate`, `modalDocLink`) were never populated, leaving the modal's default HTML placeholder values (`--`) visible if unhidden. Furthermore, if an alert referenced a bid not present in the scoped query, missing field exceptions occurred.
* **Resolution:**
  1. Added defensive validation: `if (!bid || !bid.bid_number) return;` ensures incomplete records never trigger alert modals.
  2. Fully wired all modal elements to display the active bid's tender number, category, department/ministry, verified location, and formatted IST deadline.
  3. Linked `dismissSirenModal()` to automatically call `POST /alerts/{id}/ack` to prevent duplicate popups.

### 2.3 Endless Loading State on Network / API Errors
* **Symptoms:** The table remained stuck on `"Loading verified GeM tenders..."` indefinitely if an API request failed or returned an error status.
* **Root Cause:**
  `loadDashboardData()` handled responses through `Promise.allSettled()`, but did not implement an explicit finite state machine. If `bidsRes` failed, `renderBidsTable()` was not triggered with error diagnostics.
* **Resolution:**
  Implemented a comprehensive finite state machine with six explicit lifecycle states:
  - `LOADING`: Active loading spinner with connection status.
  - `LIVE_DATA`: Real-time active procurement table with accurate counters.
  - `EMPTY_RESULTS`: Explicit empty state indicating no matching tenders for the chosen filter/categories.
  - `SOURCE_ERROR`: Diagnostic card showing GeM upstream network error with a Retry button.
  - `BACKEND_ERROR`: Diagnostic card showing server/API 500 status with a Retry button.
  - `STALE_DATA`: Warning indicator indicating background sync issue while preserving last verified snapshot.

---

## 3. End-to-End Architectural Trace

```
[GeM Portal / BidPlus API]
           │
           ▼
[official PDF Documents] (e.g., /showbidDocument/9993172)
           │
           ▼ (pypdf text & table extraction)
[pdf_location_extractor.py]
  - Page 3: Evaluation Schedule & Location of Consignee
  - Pages 15-17: Consignees/Reporting Officer table
  - Strict PIN code validation (560001 - 560110)
           │
           ▼ (Priority 1: PDF -> Priority 2: Delivery -> Priority 3: Consignee)
[location_normalizer.py]
  - Strict Bengaluru Urban inclusion
  - Strict Bengaluru Rural & Outside States rejection
           │
           ▼ (Corrigenda Date Resolution)
[corrigendum_engine / seeder.py]
  - original_end_date: 2026-10-28 13:00:00 IST
  - revised_end_date: 2026-11-20 15:00:00 IST
  - effective end_date = revised_end_date (Bid remains ACTIVE)
           │
           ▼
[FastAPI Backend: /bids/, /alerts/, /health/]
           │
           ▼ (State-Aware Dynamic Rendering)
[Executive Enterprise Dashboard: dashboard.py]
  - 7 Canonical Product Category Filters
  - Explicit State Badge (LIVE_DATA)
  - Timezone-Aware IST Timestamps & Time Remaining
  - Real-Time Siren & Alert Dispatch
```

---

## 4. Test Suite Execution & Verification

The test suite consists of 56 automated regression tests covering location normalization, category filters, PDF parsing, corrigenda date overrides, API endpoints, and alert dispatch.

```
======================== 56 passed, 1 warning in 7.05s ========================
```

| Test File | Test Cases | Status |
|:---|:---:|:---:|
| `test_corrigendum_and_pdf_audit.py` | 6 | **PASSED** |
| `test_categories_and_pdf_location.py` | 13 | **PASSED** |
| `test_bengaluru_urban_matching.py` | 7 | **PASSED** |
| `test_audit_and_upgrades.py` | 13 | **PASSED** |
| `test_gem_integration.py` | 3 | **PASSED** |
| `test_main.py` | 14 | **PASSED** |
| **Total** | **56** | **100% PASS** |
