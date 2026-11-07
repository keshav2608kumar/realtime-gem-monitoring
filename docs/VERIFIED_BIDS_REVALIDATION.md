# Verified Bids Re-Validation Report
**Project:** GeM BidWatch  
**Target Region:** Bengaluru Urban, Karnataka, India  
**Policy:** Fail-Closed Zero-Trust Verification  

---

## 1. Admission Policy for "Verified Bids"

Under the fail-closed policy, a tender is admitted to the **Verified Bids** feed (`/bids/?scope=verified`) **ONLY** when ALL of the following criteria are met:

1. **Document Identity Confirmed:**  
   The official PDF has been downloaded, checksummed, and parsed. The Bid Number on Page 1 matches the registered database Bid Number (`GEM/YYYY/B/XXXXXXX`).
2. **Delivery Location Provenance:**  
   The delivery/consignee address extracted from the PDF resolves to **Bengaluru Urban** district (PIN 560001 - 560110) or validated **Bengaluru City** (within Karnataka).
3. **Absence of Integrity Faults:**  
   The record has no active `PDF_BID_MISMATCH`, `LOCATION_MISMATCH`, `DATE_MISMATCH`, `DOCUMENT_VERSION_MISMATCH`, `OCR_UNCERTAIN`, or `SOURCE_UNAVAILABLE` flags.
4. **Lifecycle Validity:**  
   The tender is active (verified `end_date` is in the future). Expired or cancelled bids are segregated to the Expired archive.

If any of these conditions cannot be proved, admission is denied.

---

## 2. Re-Validation Status of All System Bids

### 2.1 Admitted Verified Bids

| Bid Number | Item Category | Department / Consignee | Verified PIN | Provenance Document | Status |
|---|---|---|---|---|---|
| `GEM/2026/B/8123875` | Computer Printer (V2) | ISRO Headquarters, Antariksh Bhavan, New BEL Road, Bangalore Urban | 560094 | `showbidDocument/9993172` (Page 3 verified) | **VERIFIED** |

### 2.2 Quarantined Bids (Review Queue)

The following records have been removed from the Verified feed, excluded from metrics, and quarantined in the Review Queue:

| Bid Number | Document Reference | Quarantine Classification | Audit Reason Recorded |
|---|---|---|---|
| `GEM/2026/B/8219903` | `showbidDocument/8219903` | `DOCUMENT_VERSION_MISMATCH` / `PDF_BID_MISMATCH` | Document contains `GEM/2025/B/6568333` (Battery Link Terminal in Nadiad, Gujarat - 387001), not registered 2026 bid. |
| `GEM/2026/B/8186593` | `showbidDocument/8186593` | `PDF_BID_MISMATCH` | Document contains `GEM/2025/B/6538811`, failing identity check. |
| `GEM/2026/B/8095785` | `showbidDocument/8095785` | `PDF_BID_MISMATCH` | Document contains `GEM/2025/B/6458512`, failing identity check. |
| `GEM/2026/B/8196969` | `showbidDocument/8196969` | `PDF_BID_MISMATCH` | Document contains `GEM/2025/B/6548102`, failing identity check. |
| `GEM/2026/B/8211130` | `showbidDocument/8211130` | `PDF_BID_MISMATCH` | Document contains `GEM/2025/B/6560124`, failing identity check. |
| `GEM/2026/B/8117647` | `showbidDocument/8117647` | `PDF_BID_MISMATCH` | Document contains `GEM/2025/B/6478901`, failing identity check. |
| `GEM/2026/B/8210645` | `showbidDocument/8210645` | `PDF_BID_MISMATCH` | Document contains `GEM/2025/B/6559811`, failing identity check. |
| `GEM/2026/B/8194412` | `showbidDocument/8194412` | `PDF_BID_MISMATCH` | Document contains `GEM/2025/B/6546011`, failing identity check. |
| `GEM/2026/B/8219901` | `showbidDocument/8219901` | `PDF_BID_MISMATCH` | Document contains `GEM/2025/B/6568310`, failing identity check. |
| `GEM/2026/B/8219902` | `showbidDocument/8219902` | `PDF_BID_MISMATCH` | Document contains `GEM/2025/B/6568320`, failing identity check. |
| `GEM/2026/B/8192651` | `showbidDocument/8192651` | `SOURCE_UNAVAILABLE` | PDF document missing or unreachable from GeM portal (0 bytes returned). |
| `GEM/2026/B/8192076` | `showbidDocument/8192076` | `SOURCE_UNAVAILABLE` | PDF document missing or unreachable from GeM portal (0 bytes returned). |
| `GEM/2026/B/8186128` | `showbidDocument/8186128` | `SOURCE_UNAVAILABLE` | PDF document missing or unreachable from GeM portal (0 bytes returned). |
| `GEM/2026/B/8194494` | `showbidDocument/8194494` | `SOURCE_UNAVAILABLE` | PDF document missing or unreachable from GeM portal (0 bytes returned). |
| `GEM/2026/B/8211464` | `showbidDocument/8211464` | `SOURCE_UNAVAILABLE` | PDF document missing or unreachable from GeM portal (0 bytes returned). |
| `GEM/2026/B/8192847` | `showbidDocument/8192847` | `SOURCE_UNAVAILABLE` | PDF document missing or unreachable from GeM portal (0 bytes returned). |
| `GEM/2026/B/8203999` | `showbidDocument/8203999` | `SOURCE_UNAVAILABLE` | PDF document missing or unreachable from GeM portal (0 bytes returned). |

---

## 3. Review Queue Quarantine Lifecycle

Quarantined records are safely preserved in the database to allow auditability and re-verification:
- They are visible in the dashboard under the **Review Queue** tab.
- They display a prominent red **QUARANTINED** status badge and specific mismatch chips (`PDF BID MISMATCH`, `LOCATION MISMATCH`, etc.).
- Clicking **Details** opens the inspection modal displaying the full audit history, including the registered Bid ID vs. the actual PDF Document Bid ID.
- Operators can click **Re-Extract PDF** at any time to re-query the GeM portal if corrigenda or updated documents are uploaded.
- **Alert Suppression:** No email, visual banner, or push alert can be triggered by a quarantined record.
