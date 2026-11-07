# GeM BidWatch — Corrigenda Resolution & Date Precedence Engine

**Principle:** Never treat the initial bid document deadline as final if an authoritative GeM Corrigendum extends or modifies the submission window.

---

## 1. Problem Statement

In public procurement on GeM, government buyers routinely issue **Corrigenda** to extend bid submission deadlines (due to technical queries, bidder representations, or administrative requirements).

If an application only reads the date on Page 1 of the initial PDF:
* A tender published on `16-10-2026` with an initial closing date of `28-10-2026 13:00:00` would be classified as `EXPIRED` once `28-10-2026` passes.
* However, if **Corrigendum No. 1** extended the deadline to `20-11-2026 15:00:00`, the tender is legally **ACTIVE** and open for bidding!
* Discarding the corrigendum results in severe false expirations, missing alerts, and inaccurate countdown timers.

---

## 2. Database Schema & Data Model

The `Bid` model and database schema support full date provenance:

```python
# Bid Date & Corrigendum Fields (models/bid.py)
start_date = Column(DateTime(timezone=True), nullable=True)          # Published date
end_date = Column(DateTime(timezone=True), nullable=True)            # Effective deadline used for sorting & status
original_end_date = Column(DateTime(timezone=True), nullable=True)   # Initial deadline from initial tender PDF
revised_end_date = Column(DateTime(timezone=True), nullable=True)    # Revised deadline from Corrigendum
corrigendum_status = Column(String(50), default="NONE")              # NONE, EXTENDED, CANCELLED
corrigendum_doc_url = Column(String(500), nullable=True)             # Link to Corrigendum document
corrigendum_details = Column(Text, nullable=True)                    # Corrigendum notes and rationale
date_source = Column(String(50), default="OFFICIAL_BID_DOCUMENT")    # OFFICIAL_BID_DOCUMENT, OFFICIAL_CORRIGENDUM, API_DIRECT
```

---

## 3. Date Precedence & Status Evaluation Rules

1. **Effective Deadline Calculation:**
   $$\text{effective\_deadline} = \begin{cases} 
   \text{revised\_end\_date} & \text{if } \text{corrigendum\_status} = \text{'EXTENDED'} \land \text{revised\_end\_date} \neq \text{None} \\
   \text{end\_date} & \text{otherwise}
   \end{cases}$$

2. **Active vs Expired Lifecycle:**
   - If $\text{effective\_deadline} > \text{now()}$, the tender status is **`ACTIVE`** (or `CLOSING_SOON` if within 24 hours).
   - If $\text{effective\_deadline} \le \text{now()}$, the tender status is **`EXPIRED`**.
   - If `original_end_date` is in the past, but `revised_end_date` is in the future, the tender **MUST REMAIN ACTIVE**.

3. **Time Remaining Calculation:**
   - Time remaining is dynamically computed against the effective deadline in Indian Standard Time (IST, UTC+05:30).

---

## 4. UI Representation

In the dashboard table and modal:
* **Table Deadline Column:** Shows the revised deadline (e.g., `20-11-2026 15:00 IST`) with an amber **`EXTENDED`** pill. The initial deadline is displayed struck-through underneath (`Orig: 28-10-2026`).
* **Bid Detail Modal:** Features a dedicated **Corrigendum Intelligence Section** displaying original deadline, revised deadline, date source, and official GeM Corrigendum notes.

---

## 5. Automated Verification Tests

```python
def test_corrigendum_date_override_keeps_bid_active():
    now = datetime.now(timezone.utc)
    original_past_deadline = now - timedelta(days=5)
    revised_future_deadline = now + timedelta(days=10)

    # Initial past date alone would be expired
    assert calculate_bid_status(original_past_deadline, 1, now_utc=now) == STATUS_EXPIRED

    # Effective corrigendum deadline keeps bid active
    assert calculate_bid_status(revised_future_deadline, 1, now_utc=now) == STATUS_ACTIVE
    # PASSED
```
