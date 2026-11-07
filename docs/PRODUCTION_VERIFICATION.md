# Production Verification Plan & Test Execution Report
**Target Platform:** https://realtime-gem-monitoring.onrender.com/  
**Release Version:** v2.6 (Fail-Closed Integrity & Quarantine Upgrade)  
**Verification Date:** November 2026  

---

## 1. Automated Test Suite Execution Summary

Full test execution was conducted across all 11 test suites:

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.1.1
collected 126 items

tests/test_audit_and_upgrades.py                     13 passed
tests/test_bengaluru_urban_matching.py                7 passed
tests/test_categories_and_pdf_location.py            13 passed
tests/test_corrigendum_and_pdf_audit.py               6 passed
tests/test_dashboard_navigation_upgrade.py           5 passed
tests/test_gem_integration.py                         3 passed
tests/test_location_and_alarm_removal.py             12 passed
tests/test_main.py                                   15 passed
tests/test_pdf_identity_and_fail_closed.py           12 passed
tests/test_qa_master_suite.py                        40 passed

======================= 126 passed, 1 warning in 45.79s =======================
```

### Specific Coverage of Scenarios A through J:
- **Scenario A (Correct ID + Bangalore Delivery):** PASSED -> Verified against official ISRO document `9993172` (`VERIFIED_BENGALURU_URBAN`).
- **Scenario B (Correct ID + Gujarat Delivery):** PASSED -> Document containing Gujarat address marked `LOCATION_MISMATCH` and routed to `OUTSIDE_TARGET`.
- **Scenario C (Wrong Bid ID inside PDF):** PASSED -> Marked `PDF_BID_MISMATCH` and quarantined to `AMBIGUOUS`.
- **Scenario D (2025 PDF on 2026 Bid):** PASSED -> Marked `DOCUMENT_VERSION_MISMATCH` and quarantined to `AMBIGUOUS`.
- **Scenario E (Checksum Cache & Force Re-verification):** PASSED -> Unchanged checksum preserves verification; changed checksum or force=True executes full re-audit.
- **Scenario F (Gujarat Address with Bangalore DB fallback):** PASSED -> DB text cannot override PDF evidence; marked `LOCATION_MISMATCH`.
- **Scenario G (Missing Bid ID in PDF):** PASSED -> Marked `OCR_UNCERTAIN` and routed to Review Queue; never `VERIFIED`.
- **Scenario H (Corrigendum Deadline Extension):** PASSED -> Valid corrigendum deadline keeps active status when original deadline has passed.
- **Scenario I (PDF Extraction Failure / 0 Bytes):** PASSED -> Marked `SOURCE_UNAVAILABLE` and routed to Review Queue.
- **Scenario J (Date Synchronization):** PASSED -> Start date and deadline extracted directly from official document header.

---

## 2. Live Platform Post-Deployment Checklist

Following deployment to Render (`https://realtime-gem-monitoring.onrender.com/`), execute the following verification steps:

### Test 1: Verify GEM/2026/B/8219903 Exclusion from Verified Bids
- Endpoint: `GET /bids/?scope=verified`
- **Expected:** `GEM/2026/B/8219903` is **ABSENT**. Only genuinely verified tenders (`GEM/2026/B/8123875`) are present.

### Test 2: Verify GEM/2026/B/8219903 Presence in Review Queue
- Endpoint: `GET /bids/?scope=review`
- **Expected:** `GEM/2026/B/8219903` is **PRESENT**.
- Attributes:
  - `synchronization_status`: `PDF_BID_MISMATCH`
  - `target_location_status`: `AMBIGUOUS`
  - `verification_reason`: Contains `"PDF_BID_MISMATCH: Document contains GEM/2025/B/6568333... Quarantined in Review Queue."`

### Test 3: Metric Accuracy
- Endpoint: `GET /bids/summary/stats`
- **Expected:**
  - `bengaluru_urban_verified`: `1` (representing ISRO bid `8123875`)
  - `review_count`: Quarantined bids counted correctly without polluting verified totals.

### Test 4: Alert Suppression
- Endpoint: `GET /alerts/`
- **Expected:** No active or unacknowledged alerts for `GEM/2026/B/8219903` or any quarantined tenders.
- Persistent counter on `Fired Alerts` reflects only verified matches.

### Test 5: Dashboard UI
- Open `https://realtime-gem-monitoring.onrender.com/` in browser.
- **Verified Bids tab:** Shows 1 active verified tender (`GEM/2026/B/8123875` - ISRO, Bangalore Urban).
- **Review Queue tab:** Shows quarantined tenders with red `QUARANTINED` badge and mismatch tags.
- **Details Modal on Quarantined Bid:** Displays the red Document Integrity Mismatch banner with the registered vs. PDF document Bid IDs.
