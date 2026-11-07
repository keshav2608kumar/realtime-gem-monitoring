# GeM BidWatch — Master Engineering Test Verification Report

**Report Date:** November 7, 2026  
**Test Framework:** Pytest 9.1.1 with AnyIO & Starlette TestClient  
**Target Suite:** `tests/test_audit_and_upgrades.py`, `tests/test_main.py`, `tests/test_gem_integration.py`  
**Overall Result:** **ALL 30 TESTS PASSED (100% SUCCESS)**

---

## 1. Test Suite Summary

```text
tests/test_audit_and_upgrades.py::test_location_jodhpur_never_becomes_dehradun_or_bangalore   PASSED [ 3%]
tests/test_audit_and_upgrades.py::test_location_dehradun_never_becomes_jodhpur_or_bangalore   PASSED [ 7%]
tests/test_audit_and_upgrades.py::test_location_bengaluru_normalization                       PASSED [11%]
tests/test_audit_and_upgrades.py::test_location_bangalore_urban                               PASSED [14%]
tests/test_audit_and_upgrades.py::test_location_patna_and_munger                               PASSED [18%]
tests/test_audit_and_upgrades.py::test_location_delhi                                          PASSED [22%]
tests/test_audit_and_upgrades.py::test_location_unknown_never_defaults_to_bangalore            PASSED [25%]
tests/test_audit_and_upgrades.py::test_date_parsing_various_formats                            PASSED [29%]
tests/test_audit_and_upgrades.py::test_ist_formatting                                          PASSED [33%]
tests/test_audit_and_upgrades.py::test_bid_expiry_detection                                    PASSED [37%]
tests/test_audit_and_upgrades.py::test_time_remaining_computation                              PASSED [40%]
tests/test_audit_and_upgrades.py::test_filter_matcher_prevents_empty_string_match              PASSED [44%]
tests/test_audit_and_upgrades.py::test_api_bids_lifecycle_and_sorting                          PASSED [48%]
tests/test_main.py::test_root                                                                  PASSED [51%]
tests/test_main.py::test_create_profile                                                        PASSED [55%]
tests/test_main.py::test_list_profiles                                                         PASSED [59%]
tests/test_main.py::test_update_profile                                                        PASSED [62%]
tests/test_main.py::test_delete_profile                                                        PASSED [66%]
tests/test_main.py::test_list_bids_empty                                                       PASSED [70%]
tests/test_main.py::test_batch_sync_bids                                                       PASSED [74%]
tests/test_main.py::test_devices                                                               PASSED [77%]
tests/test_main.py::test_health_status                                                         PASSED [81%]
tests/test_main.py::test_filter_matcher_keyword_match                                          PASSED [85%]
tests/test_main.py::test_filter_matcher_no_match                                               PASSED [88%]
tests/test_main.py::test_filter_matcher_no_keyword_filter                                      PASSED [92%]
tests/test_main.py::test_normalizer_basic                                                      PASSED [96%]
tests/test_main.py::test_normalizer_missing_id_returns_none                                    PASSED [100%]
tests/test_gem_integration.py::test_gem_session_refresh                                        PASSED
tests/test_gem_integration.py::test_fetch_karnataka_bids                                       PASSED
tests/test_gem_integration.py::test_fetch_toner_bids_in_bangalore                              PASSED

======================== 30 passed, 1 warning in 6.97s ========================
```

---

## 2. Key Verification Findings

1. **Location Isolation (Jodhpur vs Dehradun vs Bangalore):**
   - Jodhpur bids resolve to `Jodhpur, RAJASTHAN` and strictly reject Dehradun / Bangalore profiles.
   - Dehradun bids resolve to `Dehradun, UTTARAKHAND` and strictly reject Jodhpur / Bangalore profiles.
   - Unknown city inputs resolve to `"Not available from source"` with confidence `UNKNOWN`. Under no condition is Bangalore assigned as a fallback.
2. **Date & Time Accuracy:**
   - Publication dates and deadlines are converted to UTC and displayed accurately in `Asia/Kolkata` (IST).
   - Time remaining dynamically calculates hours, days, or past elapsed duration.
3. **Expired Bid Exclusion:**
   - Active feed `/bids/?status=active` strictly filters out expired tenders at the SQL query level.
   - Expired tenders are archived and accessible via `/bids/?status=expired`.
4. **Sorting:**
   - Multi-mode sorting (`closing_soonest`, `latest_published`, `highest_value`, etc.) operates correctly at the SQL level.
5. **Alerts & Counters:**
   - `/alerts/stats` and `/bids/summary/stats` return exact database aggregates.
   - Acknowledgement endpoints (`/alerts/{id}/ack`) update alert status to `ACKNOWLEDGED`.
