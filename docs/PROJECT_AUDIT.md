# GeM BidWatch — Complete System Architecture & Data Accuracy Audit

**Audit Date:** November 7, 2026  
**Auditor:** Antigravity High-Effort Agent Mode  
**Target Environment:** Local Workspace & Render Production (`https://realtime-gem-monitoring.onrender.com`)  
**Status:** COMPLETE AUDIT & ROOT CAUSE INVESTIGATION

---

## 1. Executive Summary & Existing Architecture

GeM BidWatch is an automated tender-tracking system designed to monitor Government e-Marketplace (GeM India) bids, detect relevant business opportunities in real-time, dispatch audible siren alarms, and maintain historical records.

### System Architecture Components
1. **Cloud Backend (`backend/app/`):**
   - **Framework:** FastAPI with Uvicorn.
   - **Database:** SQLite with SQLAlchemy ORM (`database.py`, models: `Bid`, `Profile`, `Alert`, `MonitorHealth`, `Device`).
   - **Scheduler / Poller:** APScheduler (`scheduler.py`) triggering `monitor_worker.py` every 300 seconds.
   - **API Routers:** `/bids/`, `/profiles/`, `/alerts/`, `/devices/`, `/health/`, and `/dashboard`.
   - **Notification Subsystem:** Google Firebase Cloud Messaging (`notifications/fcm_sender.py`).
2. **Web Dashboard (`backend/app/dashboard.py`):**
   - Single-file server-rendered HTML/JavaScript template utilizing Tailwind CSS and Web Audio API for browser-based sirens.
3. **Android Client (`android_app/`):**
   - Flutter application (`lib/screens/dashboard_screen.dart`, `alerts_screen.dart`, `alarm_screen.dart`, `services/alarm_service.dart`).
4. **Domestic Indian Scanner Agent (`local_scanner.py`):**
   - Standalone Python poller running within India to query GeM endpoints and synchronize newly found bids to the cloud backend via `POST /bids/batch-sync`.

---

## 2. End-to-End Data Flow

```
[GeM Portal: search-bids / all-bids-data]
                │
                ▼
   [GemFetcher: fetcher.py / local_scanner.py]
                │
                ▼
      [RawBid wrapper]
                │
                ▼
   [BidNormalizer: normalizer.py]
                │
                ▼
   [FilterMatcher: filter_matcher.py]
                │
                ▼
 [Database Ingestion: monitor_worker.py / bids.py]
                │
                ├────────────────────────┐
                ▼                        ▼
      [SQLite `bids` Table]    [SQLite `alerts` Table]
                │                        │
                ▼                        ▼
       [FastAPI Routers]        [FCM Push & Alarm]
                │
                ├────────────────────────┐
                ▼                        ▼
    [Web Dashboard JS Feed]    [Android Dashboard Feed]
```

---

## 3. Detailed Root Cause Analysis for All 12 Identified Problems

### Problem 1, 2 & 3: Incorrect Geographical Locations, Jodhpur Bids Showing Dehradun, and Bids Appearing as Bangalore

- **Root Cause A (`gem/fetcher.py` Line 123):**
  In `fetch_bids_by_keyword(keyword, page)`:
  ```python
  raw_bids = [RawBid(doc, state="KARNATAKA", city="Bangalore Urban") for doc in docs]
  ```
  When keyword search ran across the all-India catalog (`all-bids-data`), every tender returned (whether from Rajasthan, Uttarakhand, Delhi, or Bihar) was forcibly given `state="KARNATAKA"` and `city="Bangalore Urban"`.
- **Root Cause B (`gem/normalizer.py` Lines 62–63):**
  `normalize_bid(raw)` completely ignored any internal location clues in `raw.raw` (`doc`) and blindly assigned:
  ```python
  consignee_state=raw.state,
  consignee_city=raw.city,
  ```
- **Root Cause C (`seeder.py` Lines 83–84 & 101–102):**
  Startup seeder forcefully set:
  ```python
  existing.consignee_city = b.get("consignee_city", "Bangalore Urban")
  existing.consignee_state = b.get("consignee_state", "KARNATAKA")
  ```
  Every time the server booted on Render or locally, any bid missing explicit city/state was overwritten with Bangalore Urban, KARNATAKA.
- **Root Cause D (`workers/monitor_worker.py` Line 29):**
  `_get_or_create_bid` checked `Bid.gem_bid_id == bid_data.gem_bid_id`. If a bid was first fetched during a Dehradun poll, its location became "Dehradun". If the same multi-location bid was later fetched during a Jodhpur poll, `existing` was returned with the old location and never updated or segmented by consignee location.
- **Root Cause E (Frontend Hardcoded Fallbacks):**
  In `dashboard.py`:
  - Line 312: `<p id="modalLocation">Bangalore Urban, KARNATAKA</p>`
  - Line 467: `${b.consignee_city || 'Bangalore Urban'}, ${b.consignee_state || 'KARNATAKA'}`
  - Line 553–554: `const city = escapeHtml(b.consignee_city || 'Bangalore Urban');`
  In `dashboard_screen.dart`:
  - Line 769: `${bid.consigneeCity.isEmpty ? "Bangalore" : bid.consigneeCity}, ${bid.consigneeState}`
  In `alerts_screen.dart`:
  - Line 110: `${b?.consigneeCity ?? 'Bangalore'}, ${b?.consigneeState ?? 'KARNATAKA'}`

### Problem 4: Missing Publication Date
- **Root Cause:**
  `models/bid.py` and `normalizer.py` contain `start_date` (`final_start_date_sort`), but:
  - `dashboard.py` table headers contain only "Bid Deadline"; **no publication date column exists**.
  - Neither the modal, nor the cards, nor the Android dashboard display publication date/time.
  - The UI has no label or indicator when a publication date is unavailable from the source.

### Problem 5: Missing or Inconsistently Displayed Bid End Date / Deadline
- **Root Cause:**
  - In `dashboard.py` lines 555–557:
    ```javascript
    const endFormatted = b.end_date
      ? new Date(b.end_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
      : '16 Nov 2026, 03:00 PM';
    ```
    If `end_date` was missing, it fabricated `'16 Nov 2026, 03:00 PM'`.
  - Date strings from SQLite ISO format were parsed without timezone awareness (`Asia/Kolkata` vs UTC).
  - Time remaining countdown was completely missing.

### Problem 6: Expired Bids Still Displayed as Active
- **Root Cause:**
  - `routers/bids.py` query `db.query(Bid)` applies no date filtering.
  - No central `bid_status` calculation exists (e.g. `ACTIVE`, `CLOSING_SOON`, `EXPIRING_TODAY`, `EXPIRED`).
  - The frontend has no tab/toggle for Active vs Expired bids; expired tenders remain in the active stream indefinitely.

### Problem 7 & 8: Inaccurate Fired Alerts Counter & Inaccurate Alert Cards
- **Root Cause A (`dashboard.py` Line 441):**
  `document.getElementById('statAlerts').textContent = `${alerts.length} Alerts Live`;`
  `alerts` was fetched from `/alerts/?limit=20`. Therefore, the counter maxed out at 20 regardless of whether the database had 50 or 200 alerts.
- **Root Cause B (`models/alert.py`):**
  The `Alert` model lacked columns for acknowledgement (`acknowledged: bool`), alert status (`NEW`, `UNACKNOWLEDGED`, `ACKNOWLEDGED`), and match reason.
- **Root Cause C:**
  Alert cards rendered `b.consignee_city` with hardcoded fallback to `'Bangalore'`.

### Problem 9: Unreliable and Inaccurate Bid Data
- **Root Cause:**
  - No data provenance tracking: records lacked `data_source_classification` (`LIVE_VERIFIED`, `IMPORTED`, `SIMULATED`).
  - No storage of raw source payload, ingestion timestamp, or location verification confidence.
  - Synthetic data in `baseline_bids.json` was not labeled as baseline/imported.

### Problem 10: No Proper Sorting Options
- **Root Cause:**
  - In `routers/bids.py` Line 25, sorting was hardcoded to:
    `q = db.query(Bid).order_by(desc(Bid.first_seen_at))`
  - The API lacked `sort_by` parameters (e.g., `closing_soonest`, `latest_published`, `value_high`, `value_low`).
  - The Web Dashboard and Android UI lacked sorting dropdowns.

### Problem 11: Logo and Branding Need Improvement
- **Root Cause:**
  - Generic FontAwesome icon `fa-satellite-dish` and plain text with no custom SVG logo, favicon, or cohesive identity representing government procurement monitoring.

### Problem 12: Bid Feed and Database Counts Inconsistent
- **Root Cause:**
  - The dashboard stat card "Verified Bids" displayed `allBids.length` (the paginated array length, max 100), while `/health/` reported `total_bids_in_db` (actual count, e.g. 157). Users saw contradictory numbers on the same page.

---

## 4. Affected Source Files & Severity Matrix

| Component | File Path | Defect | Severity |
| :--- | :--- | :--- | :--- |
| **Backend Core** | `backend/app/models/bid.py` | Missing location model fields, date provenance, data source classification | **CRITICAL** |
| **Backend Core** | `backend/app/models/alert.py` | Missing acknowledgement status, match reason, unique constraint | **HIGH** |
| **Data Ingestion**| `backend/app/gem/fetcher.py` | Hardcoded Karnataka/Bangalore in `fetch_bids_by_keyword` | **CRITICAL** |
| **Data Ingestion**| `backend/app/gem/normalizer.py` | Blind location assignment, lack of raw provenance | **CRITICAL** |
| **Matching Engine**| `backend/app/gem/filter_matcher.py`| Substring logic flaw allowing empty string matching | **HIGH** |
| **Worker Engine** | `backend/app/workers/monitor_worker.py`| Multi-profile location collisions, no status recalculation | **HIGH** |
| **API Endpoints** | `backend/app/routers/bids.py` | Missing sorting, expired filter, and advanced query params | **HIGH** |
| **API Endpoints** | `backend/app/routers/alerts.py` | Missing alert acknowledgment endpoint and count aggregates | **MEDIUM** |
| **Startup Seeder**| `backend/app/seeder.py` | Overwrites bid locations with Bangalore fallback | **CRITICAL** |
| **Web UI** | `backend/app/dashboard.py` | Hardcoded Bangalore/deadline fallbacks, missing columns/sorts | **CRITICAL** |
| **Android Client**| `android_app/lib/screens/dashboard_screen.dart` | Hardcoded fallback locations, missing publication date | **HIGH** |
| **Local Scanner** | `local_scanner.py` | Inherits keyword-fetcher hardcoding | **HIGH** |

---

## 5. Architectural Upgrade Plan

### A. Location Architecture (Phase 3)
1. **Model Expansion (`models/bid.py`):**
   - Separate: `buyer_state`, `buyer_district`, `buyer_city`, `consignee_state`, `consignee_district`, `consignee_city`, `delivery_address`, `raw_location_text`.
   - Add: `location_verification_status` (`VERIFIED`, `NORMALIZED`, `AMBIGUOUS`, `UNKNOWN`).
2. **Dedicated Normalization Service (`services/location_normalizer.py`):**
   - Official administrative mapping covering all 36+ Indian States/UTs and key districts/cities (Jodhpur, Dehradun, Bengaluru, Delhi, Patna, etc.).
   - Explicit handling: Jodhpur maps to `Jodhpur, RAJASTHAN`; Dehradun maps to `Dehradun, UTTARAKHAND`. Neither will ever default to Bangalore.
   - Ambiguous or missing locations will be labeled `UNKNOWN` with confidence status.

### B. Date & Bid Status Engine (Phase 4 & 5)
1. **Datetime Handling (`services/datetime_service.py`):**
   - Central timezone parser enforcing `Asia/Kolkata` (IST) representation and UTC database storage.
   - Separate: `published_date`, `published_time`, `bid_end_date`, `bid_end_time`, `time_remaining`.
   - Never invent dates: display "Not available from source" if missing.
2. **Bid Status Engine (`services/bid_status_service.py`):**
   - Statuses: `ACTIVE`, `CLOSING_SOON` (<24h), `EXPIRING_TODAY`, `EXPIRED`, `CANCELLED`, `COMPLETED`, `UNKNOWN`.
   - Default query excludes `EXPIRED` unless explicitly requested via `status=expired`.

### C. Sorting, Searching & Aggregates (Phase 6 & 7)
1. **Server-Side Sorting (`routers/bids.py`):**
   - `latest_published`, `oldest_published`, `closing_soonest`, `closing_latest`, `newly_added`, `recently_updated`, `value_high`, `value_low`.
2. **True Fired Alerts Counter (`routers/alerts.py`):**
   - Endpoint returning exact database counts: `total_alerts`, `new_alerts`, `unacknowledged_alerts`, `acknowledged_alerts`.
   - Distinct alert acknowledgement endpoints (`POST /alerts/{id}/ack`).

### D. Professional UI & Branding (Phase 8 & 9)
1. **Brand Identity:**
   - Vector SVG logo: Shield/Radar icon combined with tender document and location pin.
   - Dark/Light enterprise dashboard palette.
2. **Bid Feed Redesign:**
   - Clear publication and deadline columns with time remaining badge.
   - Location chip showing city, state, and verification badge.
   - Data source classification tag (`LIVE VERIFIED`, `IMPORTED`, `SIMULATED`).

---

## 6. Prioritized Implementation Checklist

- [ ] **Step 1:** Create `gem_bidwatch/docs/` baseline documentation.
- [ ] **Step 2:** Implement `LocationNormalizer` service with verified administrative dictionary.
- [ ] **Step 3:** Implement `DateTimeService` & `BidStatusService` for IST & expiry management.
- [ ] **Step 4:** Upgrade `models/bid.py` and `models/alert.py` database schema.
- [ ] **Step 5:** Fix `gem/fetcher.py`, `gem/normalizer.py`, and `seeder.py` (eliminate hardcoded fallbacks).
- [ ] **Step 6:** Upgrade `routers/bids.py` (sorting, status filter, location search) & `routers/alerts.py`.
- [ ] **Step 7:** Redesign Web Dashboard (`dashboard.py`) with enterprise branding, SVG logo, sorting, filters, and accurate columns.
- [ ] **Step 8:** Update Android App (`dashboard_screen.dart`, `alerts_screen.dart`) removing fallbacks and reflecting new schema.
- [ ] **Step 9:** Build comprehensive automated test suite (Location tests, Date tests, Expiry tests, Alert tests, Sorting tests).
- [ ] **Step 10:** Verify deployment readiness and complete all 10 required docs.
