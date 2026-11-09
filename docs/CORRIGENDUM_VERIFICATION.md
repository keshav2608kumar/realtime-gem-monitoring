# GeM BidWatch — Corrigendum & Deadline Resolution Report
**Module:** `backend/app/services/datetime_service.py` & `backend/app/services/bid_status_service.py`  
**Date:** 09 November 2026  

---

## 1. Overview & Business Rules

Government tenders frequently undergo deadline extensions, technical clarifications, or corrigenda published days after initial issue. The system enforces an authoritative precedence hierarchy to calculate the true operational deadline:

1. **Official GeM Corrigendum (`revised_end_date`):** If a corrigendum extends the bid deadline, it supersedes the original document date.
2. **Authoritative GeM Portal Structured Data:** Used if corrigendum document extraction is in progress.
3. **Original Bid Document (`original_end_date`):** Used as baseline fallback.

---

## 2. Dynamic Lifecycle Status Engine

All dates are converted to Indian Standard Time (`Asia/Kolkata`, UTC+5:30) for display and comparisons.

| Condition | Status | Action in UI Feed |
|---|---|---|
| `end_date > now + 24 hours` | `ACTIVE` | Displayed in Verified Bids |
| `now < end_date <= now + 24 hours` | `CLOSING_SOON` | Amber Badge, Countdown (< 24h) |
| `end_date <= now` | `EXPIRED` | Excluded from Active Feed (Grey Badge in All/Expired filter) |
| `status == 2` | `CANCELLED` | Red Badge |
| Date Conflict / Mismatch | `DATA_MISMATCH` | Quarantined to Review Queue |

---

## 3. Verified Example (`GEM/2026/B/8123875` - ISRO Antariksh Bhavan)
- **Original End Date:** 28-10-2026 13:00:00 IST
- **Corrigendum No. 1:** Extended deadline to 20-11-2026 15:00:00 IST
- **System Behavior:** Automatically recognized Corrigendum No. 1, updated effective deadline to 20-11-2026, and maintained `ACTIVE` status instead of falsely marking the tender expired.
