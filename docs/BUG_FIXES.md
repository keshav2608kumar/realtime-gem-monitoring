# GeM BidWatch — Bug Fixes & Audit Resolution Log

This document records each identified issue, its verified root cause, the files modified, the implemented engineering fix, and the test verification results.

---

### Bug 1: Bids from Different Locations Appearing as Bangalore
- **Original Problem:** All bids fetched across India (or with missing location) displayed "Bangalore" or "Bangalore Urban, KARNATAKA".
- **Root Cause:**
  1. `backend/app/gem/fetcher.py` line 123 hardcoded `state="KARNATAKA", city="Bangalore Urban"` in `fetch_bids_by_keyword()`.
  2. `backend/app/gem/normalizer.py` assigned `consignee_state=raw.state` and `consignee_city=raw.city` without administrative validation.
  3. `backend/app/seeder.py` used `b.get("consignee_city", "Bangalore Urban")` fallback.
  4. Frontend templates (`dashboard.py` and `dashboard_screen.dart`) used `|| 'Bangalore Urban'`.
- **Files Changed:**
  - `backend/app/gem/fetcher.py`
  - `backend/app/gem/normalizer.py`
  - `backend/app/services/location_normalizer.py`
  - `backend/app/seeder.py`
  - `backend/app/dashboard.py`
  - `android_app/lib/screens/dashboard_screen.dart`
  - `android_app/lib/screens/alerts_screen.dart`
- **Implemented Solution:**
  Removed all hardcoded Bangalore fallbacks. Created `LocationNormalizer` service with canonical registry for all 36+ Indian States/UTs and key districts. Unknown locations are explicitly labeled "Not available from source" and given confidence `UNKNOWN`.
- **Test Performed:** `tests/test_audit_and_upgrades.py::test_location_unknown_never_defaults_to_bangalore`
- **Result:** PASSED (Displays "Not available from source", never Bangalore).

---

### Bug 2: Jodhpur Bids Showing Dehradun or Other Locations
- **Original Problem:** Bids from Jodhpur (Rajasthan) appeared as Dehradun (Uttarakhand) or vice-versa.
- **Root Cause:**
  1. In `gem/filter_matcher.py` lines 46–47, `if c_clean and (c_clean in bid_city or bid_city in c_clean):` evaluated `"" in c_clean` as `True` when `bid_city` was empty, matching any city in any profile.
  2. In `monitor_worker.py`, `_get_or_create_bid` reused an existing bid record without segmenting by consignee location.
- **Files Changed:**
  - `backend/app/gem/filter_matcher.py`
  - `backend/app/services/location_normalizer.py`
  - `backend/app/workers/monitor_worker.py`
- **Implemented Solution:**
  Enforced strict administrative location resolution. Jodhpur strictly maps to `Jodhpur, RAJASTHAN`. Dehradun strictly maps to `Dehradun, UTTARAKHAND`. Substring matching on empty strings was eliminated.
- **Tests Performed:**
  - `tests/test_audit_and_upgrades.py::test_location_jodhpur_never_becomes_dehradun_or_bangalore`
  - `tests/test_audit_and_upgrades.py::test_location_dehradun_never_becomes_jodhpur_or_bangalore`
  - `tests/test_audit_and_upgrades.py::test_filter_matcher_prevents_empty_string_match`
- **Result:** PASSED (Jodhpur and Dehradun remain 100% distinct).

---

### Bug 3: Publication Date Missing
- **Original Problem:** Publication date/time was not shown in the Web Dashboard or Android feed.
- **Root Cause:**
  The `dashboard.py` table had no published date column. `models/bid.py` had `start_date`, but the UI never formatted or presented it to users.
- **Files Changed:**
  - `backend/app/schemas/__init__.py`
  - `backend/app/routers/bids.py`
  - `backend/app/services/datetime_service.py`
  - `backend/app/dashboard.py`
  - `android_app/lib/screens/dashboard_screen.dart`
  - `android_app/lib/models/models.dart`
- **Implemented Solution:**
  Extracted `final_start_date_sort` from GeM payload. Converted to UTC and formatted in Indian Standard Time (`Asia/Kolkata`). Added dedicated "Published Date (IST)" column on the web table and published timestamp chips on Android cards. Missing publication dates show "Not available from source" rather than current ingestion date.
- **Test Performed:** `tests/test_audit_and_upgrades.py::test_ist_formatting`
- **Result:** PASSED.

---

### Bug 4: Bid End Date / Deadline Missing or Inconsistently Displayed
- **Original Problem:** Deadlines were missing or showed fabricated fallbacks like `'16 Nov 2026, 03:00 PM'`.
- **Root Cause:**
  `dashboard.py` lines 555–557 had a hardcoded ternary fallback: `: '16 Nov 2026, 03:00 PM'`.
- **Files Changed:**
  - `backend/app/dashboard.py`
  - `backend/app/services/datetime_service.py`
  - `backend/app/routers/bids.py`
- **Implemented Solution:**
  Removed fabricated fallback string. Datetimes are parsed with full timezone support and formatted as `DD Mon YYYY, hh:mm AM/PM IST`. Added human-readable time remaining countdown.
- **Test Performed:** `tests/test_audit_and_upgrades.py::test_time_remaining_computation`
- **Result:** PASSED.

---

### Bug 5: Expired Bids Still Displayed as Active
- **Original Problem:** Bids with past deadlines remained visible in the main active feed.
- **Root Cause:**
  `routers/bids.py` did not check `end_date` against current time. No status segregation existed.
- **Files Changed:**
  - `backend/app/services/bid_status_service.py`
  - `backend/app/routers/bids.py`
  - `backend/app/dashboard.py`
- **Implemented Solution:**
  Created `BidStatusService` with states: `ACTIVE`, `CLOSING_SOON`, `EXPIRING_TODAY`, `EXPIRED`, `CANCELLED`, `COMPLETED`, `UNKNOWN`. Default query `/bids/?status=active` excludes expired bids. Expired tenders are archived under a separate "Expired Archive" tab.
- **Test Performed:** `tests/test_audit_and_upgrades.py::test_bid_expiry_detection`
- **Result:** PASSED.

---

### Bug 6: Fired Alerts Counter Inaccurate
- **Original Problem:** Fired Alerts counter on web dashboard capped at 20 or showed contradictory counts.
- **Root Cause:**
  `dashboard.py` calculated counter from paginated array length `alerts.length` (fetched with `/alerts/?limit=20`), rather than database aggregate.
- **Files Changed:**
  - `backend/app/routers/alerts.py`
  - `backend/app/dashboard.py`
  - `backend/app/schemas/__init__.py`
- **Implemented Solution:**
  Added `/alerts/stats` endpoint returning exact counts: `total_alerts`, `new_alerts`, `unacknowledged_alerts`, `acknowledged_alerts`.
- **Test Performed:** `tests/test_audit_and_upgrades.py::test_api_bids_lifecycle_and_sorting`
- **Result:** PASSED.

---

### Bug 7: Alert Cards Show Inaccurate Information
- **Original Problem:** Alert cards showed hardcoded Bangalore locations or lacked match details.
- **Root Cause:**
  Alert records lacked match reasons, acknowledgement state, and proper joinedload serialization.
- **Files Changed:**
  - `backend/app/models/alert.py`
  - `backend/app/routers/alerts.py`
  - `android_app/lib/screens/alerts_screen.dart`
- **Implemented Solution:**
  Added `status`, `acknowledged`, `acknowledged_at`, and `match_reason` to `Alert`. Enriched alert responses with complete bid details and verified location. Added `POST /alerts/{id}/ack` for acknowledgement.
- **Test Performed:** `tests/test_audit_and_upgrades.py::test_api_bids_lifecycle_and_sorting`
- **Result:** PASSED.

---

### Bug 8: No Proper Sorting Options
- **Original Problem:** Only ingestion timestamp sorting (`desc(Bid.first_seen_at)`) was supported; no UI sorting dropdown existed.
- **Root Cause:**
  `routers/bids.py` lacked query sorting parameters.
- **Files Changed:**
  - `backend/app/routers/bids.py`
  - `backend/app/dashboard.py`
- **Implemented Solution:**
  Added 8 sorting modes: `closing_soonest`, `latest_published`, `oldest_published`, `closing_latest`, `newly_added`, `recently_updated`, `highest_value`, `lowest_value`. Added professional sorting dropdown on web dashboard.
- **Test Performed:** `tests/test_audit_and_upgrades.py::test_api_bids_lifecycle_and_sorting`
- **Result:** PASSED.

---

### Bug 9: Logo and Branding Need Improvement
- **Original Problem:** Generic FontAwesome satellite icon and plain text without distinctive identity.
- **Files Changed:**
  - `backend/app/static/logo.svg`
  - `backend/app/dashboard.py`
- **Implemented Solution:**
  Designed custom geometric SVG emblem combining radar monitoring shield, concentric arcs, procurement tender sheet, and alarm beacon. Integrated into navbar and favicon.
- **Result:** Clean enterprise branding deployed.

---

### Bug 10: Inconsistent Feed and Database Counts
- **Original Problem:** Web dashboard displayed `100 Verified` (paginated length) while `/health/` reported `157` total bids.
- **Root Cause:**
  `statBidsCount` used `allBids.length` instead of `/bids/summary/stats` database total.
- **Files Changed:**
  - `backend/app/routers/bids.py`
  - `backend/app/dashboard.py`
- **Implemented Solution:**
  Added `/bids/summary/stats` returning verified database counts: `total_bids`, `active_bids`, `expired_bids`. Dashboard displays exact database counts.
- **Result:** PASSED.
