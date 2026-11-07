# GeM BidWatch — Alert Creation & Counter Accuracy Specification

This document details the alert matching pipeline, notification dispatch, acknowledgement lifecycle, and exact database counter calculation implemented in `app.gem.filter_matcher`, `models.alert`, and `routers.alerts`.

---

## 1. Alert Generation Criteria

An alert record is created in the database **only** when all of the following conditions are simultaneously met:
1. **Real Ingested Bid:** The tender is a verified `Bid` record in the database.
2. **Normalized Location Match:**
   - If the active monitoring profile defines a `state`, the bid's canonical state must match exactly.
   - If the profile defines `cities`, the bid's canonical city must match one of the profile cities.
   - Bids with missing location fields will **not** match location-restricted profiles.
3. **Keyword Boundary Match:**
   - The category text must contain at least one configured keyword with regex word boundary awareness (e.g. `\bprinter\b`, `\bink(?:jet|s)?\b`, `\bc(?:a|ar)tridge\b`).
   - Prevents false positives such as `ink` matching `Drinking water`.
4. **Ministry Filter (Optional):**
   - If configured, the procuring ministry must be included in the profile's allowed list.
5. **Deduplication:**
   - The database enforces a `UniqueConstraint('profile_id', 'bid_id', name='uq_profile_bid')`.
   - An alert is created at most once per profile-bid pair.

---

## 2. Alert Lifecycle States

- **`NEW`**: Alert created, unviewed and unacknowledged by user.
- **`UNACKNOWLEDGED`**: Alert dispatched or viewed in feed, awaiting user action.
- **`ACKNOWLEDGED`**: User explicitly clicked "Acknowledge" or "Dismiss & Mute".

---

## 3. Accurate Counter Calculations

The Fired Alerts counters are strictly calculated via database SQL aggregates, never from frontend array slicing:

- **Total Alerts:**
  `SELECT count(*) FROM alerts;`
- **New Alerts:**
  `SELECT count(*) FROM alerts WHERE status = 'NEW';`
- **Unacknowledged Alerts:**
  `SELECT count(*) FROM alerts WHERE acknowledged = 0;`
- **Acknowledged Alerts:**
  `SELECT count(*) FROM alerts WHERE acknowledged = 1;`
- **Dispatched Push Notifications:**
  `SELECT count(*) FROM alerts WHERE notification_sent = 1;`
- **Failed Notifications:**
  `SELECT count(*) FROM alerts WHERE notification_error IS NOT NULL;`

Endpoint `GET /alerts/stats` exposes these numbers to both the Web Dashboard and Android Client.
