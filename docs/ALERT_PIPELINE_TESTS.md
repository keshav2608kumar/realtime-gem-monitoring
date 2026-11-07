# GeM BidWatch — Real-Time Alert & Siren Dispatch Pipeline Audit

**Feature:** Real-time procurement match detection, sticky alert banner, and audio siren notification.  
**Audited Components:** `Alert` model, `/alerts/` REST API endpoints, `filter_matcher.py`, `dashboard.py` alert banner & siren oscillator.

---

## 1. Alert Lifecycle & Matching Engine

The alert engine continuously monitors incoming and synced tenders against active monitoring profiles:

```
[Ingested Tender] ───► [Strict Scope Check: Bengaluru Urban]
                               │
                               ▼
                   [Category Filter Match] (1 of 7 Canonical Categories)
                               │
                               ▼
                   [Keyword / Minimum Value Filter]
                               │
                               ▼
                   [Alert Generation: Alert(status='NEW', acknowledged=False)]
                               │
                               ▼
                   [WebSocket / Polling Dispatch: /alerts/?unacknowledged_only=true]
                               │
                               ▼
                   [Client Sticky Banner + Red Alert Siren Modal]
```

---

## 2. Root Cause & Repair of Incomplete Modal (`--`)

### The Bug:
When `checkUnacknowledgedAlerts()` received an unacknowledged alert:
1. It invoked `renderActiveBanner(topAlert, bid)` to populate the sticky top banner.
2. However, the DOM elements for the full-screen siren modal:
   - `modalTenderNo`
   - `modalCategory`
   - `modalDept`
   - `modalLocation`
   - `modalEndDate`
   - `modalDocLink`
   were never set. If the modal was displayed, it presented the raw static template text (`--`), giving the false appearance of missing or corrupted bid records.
3. If an alert referenced a bid that was not included in the scoped dataset, `topAlert.bid` was incomplete.

### The Fix:
* Added strict defensive check:
  ```javascript
  if (!bid || !bid.bid_number) return;
  ```
* Explicitly populate all modal elements with the active bid's real attributes:
  ```javascript
  document.getElementById('modalTenderNo').textContent = bid.bid_number;
  document.getElementById('modalCategory').textContent = bid.category_name || 'GeM Procurement';
  document.getElementById('modalDept').textContent = bid.dept_name || bid.ministry_name || 'Government Organization';
  document.getElementById('modalLocation').textContent = bid.display_location || 'Bengaluru Urban, Karnataka';
  document.getElementById('modalEndDate').textContent = `${bid.end_date_formatted || 'N/A'} (${bid.end_time_formatted || ''} IST)`;
  document.getElementById('modalDocLink').href = bid.bid_url || '#';
  ```
* Integrated `POST /alerts/{id}/ack` into `dismissSirenModal()` so acknowledging or muting an alert immediately updates the server and stops re-triggering.

---

## 3. Web Audio Siren Oscillator

* **Oscillator Type:** Dual-frequency alternating sawtooth wave (`800 Hz` and `1200 Hz`) modulating every 350ms.
* **Volume Control:** Normalized gain node (`0.25`) to prevent clipping.
* **Mute Persistence:** Supports one-click muting (`Siren: MUTED`) with mute status preserved in session memory.
* **Browser Autoplay Compliance:** Web Audio context automatically resumes on user gesture (`click`, `scroll`, or `touch`).

---

## 4. Automated API & Integration Tests

Verified via `pytest backend/tests/test_main.py` and `pytest backend/tests/test_audit_and_upgrades.py`:
* `test_filter_matcher_keyword_match`: **PASSED**
* `test_filter_matcher_no_match`: **PASSED**
* `test_filter_matcher_no_keyword_filter`: **PASSED**
* `test_profile_matcher_strict_bengaluru_urban`: **PASSED**
* `test_profile_matcher_with_category_filter`: **PASSED**
