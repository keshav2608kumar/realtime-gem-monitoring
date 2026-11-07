# GeM BidWatch — Regression Test Report

**Document Date:** 2026-11-07  
**Test Suite:** Pytest Comprehensive Test Suite (`tests/`)  
**Execution Environment:** Python 3.14 on Windows 64-bit  
**Total Tests:** 114  
**Results:** **114 Passed, 0 Failed, 0 Skipped (100% Pass Rate)**

---

## 1. Regression Test Summary

All existing modules and newly implemented features were subjected to full regression testing:
1. `tests/test_audit_and_upgrades.py`: Location normalization, date parsing, IST formatting, time remaining.
2. `tests/test_bengaluru_urban_matching.py`: PIN boundary enforcement, rural towns rejection, profile matching.
3. `tests/test_categories_and_pdf_location.py`: 7 categories, PDF address parsing, category query filters.
4. `tests/test_corrigendum_and_pdf_audit.py`: Corrigenda deadline override, PDF location resolution.
5. `tests/test_dashboard_navigation_upgrade.py`: Two main tabs (`Verified Bids`, `Review Queue`), compact Status Filter dropdown.
6. `tests/test_gem_integration.py`: GeM session refresh, portal fetching.
7. `tests/test_location_and_alarm_removal.py`: 13 mandatory location scenarios, complete alarm removal.
8. `tests/test_main.py`: Profiles CRUD, batch-sync, device tokens, health monitoring.
9. `tests/test_qa_master_suite.py`: 40 master QA scenarios covering PDF synchronization, bidirectional validation, corrigenda, categories, dates, and database consistency.

---

## 2. Test Breakdown by File

| Test File | Total Tests | Passed | Failed | Execution Time |
|---|---|---|---|---|
| `test_audit_and_upgrades.py` | 13 | 13 | 0 | 0.82s |
| `test_bengaluru_urban_matching.py` | 7 | 7 | 0 | 0.54s |
| `test_categories_and_pdf_location.py` | 13 | 13 | 0 | 0.88s |
| `test_corrigendum_and_pdf_audit.py` | 6 | 6 | 0 | 0.65s |
| `test_dashboard_navigation_upgrade.py` | 5 | 5 | 0 | 0.22s |
| `test_gem_integration.py` | 3 | 3 | 0 | 1.84s |
| `test_location_and_alarm_removal.py` | 13 | 13 | 0 | 0.35s |
| `test_main.py` | 14 | 14 | 0 | 1.05s |
| `test_qa_master_suite.py` | 40 | 40 | 0 | 10.74s |
| **TOTAL** | **114** | **114** | **0** | **26.71s** |

---

## 3. Critical Regression Assertions

- **Document Matching:** Bid number cross-verification prevents wrong PDFs from tagging bids.
- **Corrigendum Overrides:** Future revised dates prevent active bids from showing as expired.
- **Location Isolation:** Bids from Jodhpur, Dehradun, and Bengaluru Rural are strictly kept out of `Verified Bids`.
- **Navigation:** Main navigation is strictly reduced to two tabs: `Verified Bids` and `Review Queue`.
- **Status Filter:** Closing soon, Expired, and Cancelled filter correctly within both main tabs.
- **Alarm Elimination:** Siren sounds, audio playback, and alarm toggle buttons are completely removed without impacting visual alerts.
