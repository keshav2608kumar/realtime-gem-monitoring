# PDF-to-Bid Identity Audit Report
**Project:** GeM BidWatch  
**Severity:** Critical P0 (Data Integrity Failure Resolved)  
**Date:** November 2026  
**Auditor:** Lead QA & Systems Integrity Engineer  

---

## 1. Executive Summary

A critical data integrity failure was detected on the live platform where tender record `GEM/2026/B/8219903` was falsely displayed as a verified Bengaluru Urban bid:
- **Displayed Publication Date:** 06 November 2026
- **Displayed Deadline:** 27 November 2026
- **Displayed Delivery Location:** Bengaluru Urban, Karnataka - 560038 (Page 9)
- **Displayed Status:** MATCH / IMPORTED

Manual download and binary extraction of the authoritative document from GeM portal (`https://bidplus.gem.gov.in/showbidDocument/8219903`) revealed:
- **True Bid Number inside Document:** `GEM/2025/B/6568333`
- **True Publication Date:** 13-08-2025
- **True Item Category:** Battery Link Terminal
- **True Consignee & Delivery Location:** Sodha Naranbhai Shanabhai, Gujarat State Road Transport Corporation (GSRTC), Central Workshop, Nadiad, Kheda, **GUJARAT - 387001**

The PDF was not a 2026 Bangalore tender; it was a 2025 Gujarat battery terminal tender. This report documents the exact mechanism of failure, the baseline inventory audit, and the permanent identity verification engine implemented to prevent recurrence.

---

## 2. Technical Root Cause of False Verification

### 2.1 GeM Document ID vs. Public Bid Number
In the Government e-Marketplace (GeM) architecture, the URL path:
`https://bidplus.gem.gov.in/showbidDocument/<ID>`
uses an internal system document ID (`b_id`), which **does NOT equal** the public alphanumeric bid number (`GEM/YYYY/B/XXXXXXX`).
In previous versions of the ingestion scripts, the trailing integer from `GEM/2026/B/8219903` (`8219903`) was incorrectly assumed to be the document ID for that bid. Requesting document `8219903` returned a completely different tender created in 2025 in Gujarat (`GEM/2025/B/6568333`).

### 2.2 Lack of Bid Identity Verification in PDF Parser
The legacy PDF parser extracted text from the last page to search for PIN codes, but **never validated the Bid Number header on Page 1** of the PDF against the database record's `bid_number`. As a result, the parser extracted the Gujarat address but failed to reject the document.

### 2.3 Blind Seeder Fallback & False Alert Generation
In `backend/app/seeder.py`, lines 100 and 158 contained the dangerous fallback:
```python
# DEFECTIVE LEGACY LOGIC:
existing.target_location_status = b.get("target_location_status") or loc.target_status or "VERIFIED_BENGALURU_URBAN"
```
Furthermore, the seeder created alerts for every active profile against all ingested bids, regardless of whether document verification had succeeded.

---

## 3. Comprehensive Baseline Bid Inventory Audit

All 18 records in `backend/app/baseline_bids.json` were audited by retrieving and analyzing their linked official documents:

| # | Registered Bid Number | Internal Doc ID | Actual Doc Bid Number | Actual Location Found | Verification Outcome | Action Taken |
|---|-----------------------|-----------------|-----------------------|-----------------------|----------------------|--------------|
| 1 | `GEM/2026/B/8123875` | `9993172` | `GEM/2026/B/8123875` | ISRO HQ, Bangalore Urban - 560094 | **VERIFIED** | Retained in Verified Bids |
| 2 | `GEM/2026/B/8186593` | `8186593` | `GEM/2025/B/6538811` | Mismatched Document | **PDF_BID_MISMATCH** | Quarantined to Review Queue |
| 3 | `GEM/2026/B/8095785` | `8095785` | `GEM/2025/B/6458512` | Mismatched Document | **PDF_BID_MISMATCH** | Quarantined to Review Queue |
| 4 | `GEM/2026/B/8192651` | `8192651` | N/A (0 bytes / 404) | Document Missing | **SOURCE_UNAVAILABLE** | Quarantined to Review Queue |
| 5 | `GEM/2026/B/8192076` | `8192076` | N/A (0 bytes / 404) | Document Missing | **SOURCE_UNAVAILABLE** | Quarantined to Review Queue |
| 6 | `GEM/2026/B/8186128` | `8186128` | N/A (0 bytes / 404) | Document Missing | **SOURCE_UNAVAILABLE** | Quarantined to Review Queue |
| 7 | `GEM/2026/B/8196969` | `8196969` | `GEM/2025/B/6548102` | Mismatched Document | **PDF_BID_MISMATCH** | Quarantined to Review Queue |
| 8 | `GEM/2026/B/8211130` | `8211130` | `GEM/2025/B/6560124` | Mismatched Document | **PDF_BID_MISMATCH** | Quarantined to Review Queue |
| 9 | `GEM/2026/B/8117647` | `8117647` | `GEM/2025/B/6478901` | Mismatched Document | **PDF_BID_MISMATCH** | Quarantined to Review Queue |
| 10 | `GEM/2026/B/8210645` | `8210645` | `GEM/2025/B/6559811` | Mismatched Document | **PDF_BID_MISMATCH** | Quarantined to Review Queue |
| 11 | `GEM/2026/B/8194494` | `8194494` | N/A (0 bytes / 404) | Document Missing | **SOURCE_UNAVAILABLE** | Quarantined to Review Queue |
| 12 | `GEM/2026/B/8211464` | `8211464` | N/A (0 bytes / 404) | Document Missing | **SOURCE_UNAVAILABLE** | Quarantined to Review Queue |
| 13 | `GEM/2026/B/8194412` | `8194412` | `GEM/2025/B/6546011` | Mismatched Document | **PDF_BID_MISMATCH** | Quarantined to Review Queue |
| 14 | `GEM/2026/B/8192847` | `8192847` | N/A (0 bytes / 404) | Document Missing | **SOURCE_UNAVAILABLE** | Quarantined to Review Queue |
| 15 | `GEM/2026/B/8203999` | `8203999` | N/A (0 bytes / 404) | Document Missing | **SOURCE_UNAVAILABLE** | Quarantined to Review Queue |
| 16 | `GEM/2026/B/8219901` | `8219901` | `GEM/2025/B/6568310` | Mismatched Document | **PDF_BID_MISMATCH** | Quarantined to Review Queue |
| 17 | `GEM/2026/B/8219902` | `8219902` | `GEM/2025/B/6568320` | Mismatched Document | **PDF_BID_MISMATCH** | Quarantined to Review Queue |
| 18 | `GEM/2026/B/8219903` | `8219903` | `GEM/2025/B/6568333` | GSRTC, Nadiad, Gujarat - 387001 | **DOCUMENT_VERSION_MISMATCH / PDF_BID_MISMATCH** | Quarantined to Review Queue |

**Conclusion:** Only **1 bid** (`GEM/2026/B/8123875`) is a genuine, verified Bengaluru Urban tender with matching document provenance. The other 17 records lacked valid matching official documents and were quarantined.

---

## 4. Fail-Closed Document Verification Engine

We implemented a zero-trust, fail-closed verification pipeline in `backend/app/services/pdf_synchronizer.py`:

```
                 Incoming Bid Document PDF
                            │
               ┌────────────┴────────────┐
               ▼                         ▼
         Is Document Present?       No ──► STATUS: SOURCE_UNAVAILABLE
               │                           Target: UNKNOWN (Review Queue)
              Yes
               ▼
     Extract Page 1 Header Metadata
               │
               ▼
       Bid Number Match?
       (PDF Bid == Record Bid)
               ├── No (Year mismatch) ───► STATUS: DOCUMENT_VERSION_MISMATCH
               ├── No (ID mismatch) ─────► STATUS: PDF_BID_MISMATCH
               │                           Target: AMBIGUOUS (Review Queue)
              Yes
               ▼
   Extract Consignee/Delivery Address
               │
               ▼
     Delivery in Bengaluru Urban?
               ├── Outside State/Rural ──► STATUS: LOCATION_MISMATCH
               │                           Target: OUTSIDE_TARGET (Excluded)
               ├── Uncertain/Ambiguous ──► STATUS: OCR_UNCERTAIN
               │                           Target: AMBIGUOUS (Review Queue)
              Yes
               ▼
     STATUS: VERIFIED
     Target: VERIFIED_BENGALURU_URBAN
     (Admitted to Verified Bids)
```

### Key Verification Rules:
1. **Bid Identity Check:** `clean_pdf_bid == clean_expected_bid`. If different, immediately abort verification, assign `PDF_BID_MISMATCH` or `DOCUMENT_VERSION_MISMATCH`, record audit reason, and quarantine to `AMBIGUOUS`.
2. **Location Proof Check:** The location must come from the PDF evidence itself. Database buyer office or department names **CANNOT** override an out-of-target delivery location found in the PDF.
3. **Alert Authorization:** Alerts are generated **ONLY IF** `synchronization_status == "VERIFIED"` and `target_location_status in ("VERIFIED_BENGALURU_URBAN", "VERIFIED_BENGALURU_CITY")`. Invalid alerts on quarantined bids are purged automatically during startup.
