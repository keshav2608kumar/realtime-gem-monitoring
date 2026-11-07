# GeM BidWatch — Bid Lifecycle & Status Rules

This document specifies the authoritative rules for bid status calculation, active vs. expired segregation, and corrigendum handling implemented in `app.services.bid_status_service`.

---

## 1. Lifecycle Statuses

Every tender in the system is evaluated against its verified closing date and official GeM status flags:

| Status Code | Description | Condition | Active in Main Feed? |
| :--- | :--- | :--- | :--- |
| **`ACTIVE`** | Ongoing opportunity with standard window. | `end_date > now + 24 hours` and `b_status == 1` | **YES** |
| **`CLOSING_SOON`** | Tender closes in 24 hours or less. | `now < end_date <= now + 24 hours` | **YES** (Highlighted Amber) |
| **`EXPIRING_TODAY`** | Tender closes today in IST timezone. | `end_date.date() == now_ist.date()` | **YES** (Urgent Badge) |
| **`EXPIRED`** | Verified deadline has elapsed. | `end_date <= now` | **NO** (Archived to Expired tab) |
| **`CANCELLED`** | Withdrawn or cancelled by buyer organization. | `b_status == 2` | **NO** |
| **`COMPLETED`** | Financial bid opened / contract awarded. | `b_status == 3` | **NO** |
| **`UNKNOWN`** | End date unavailable or record malformed. | `end_date is None` | **NO** (Requires Reconciliation) |

---

## 2. Dynamic Recalculation & Feed Segregation

1. **Query Filtering (`routers/bids.py`):**
   - **`/bids/?status=active` (Default):**
     Executes `WHERE end_date > now OR end_date IS NULL`. Expired records are excluded at the database level.
   - **`/bids/?status=closing_soon`:**
     Executes `WHERE end_date > now AND end_date <= now + 24 hours`.
   - **`/bids/?status=expired`:**
     Executes `WHERE end_date <= now`.
   - **`/bids/?status=all`:**
     Returns all records regardless of status.
2. **Corrigendum Deadline Modifications:**
   - When a corrigendum is published on GeM extending the bid deadline, the updated `end_date` is ingested via `batch-sync` or poller.
   - The status is immediately recalculated. If a previously expired tender has its deadline extended, it returns to `ACTIVE`.
   - The `updated_at` timestamp is refreshed.
