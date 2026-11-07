# Data Integrity Failure Root Cause Analysis
**Incident:** False Verification of `GEM/2026/B/8219903` & Out-of-Target Tenders  
**Status:** Permanently Resolved & Tested  
**Components Involved:** `seeder.py`, `pdf_synchronizer.py`, `bids.py`, `baseline_bids.json`  

---

## 1. Problem Statement

On the live production site `https://realtime-gem-monitoring.onrender.com/`, the record `GEM/2026/B/8219903` appeared in the **Verified Bids** feed with a green badge, indicating a verified delivery location in Bangalore Urban (PIN 560038). When user opened the linked document, the document was from 2025 (`GEM/2025/B/6568333`) and specified delivery in Nadiad, Gujarat.

---

## 2. In-Depth Root Cause Chain

Five distinct system bugs interacted to cause this failure:

### Bug 1: Conflation of GeM Document ID with Bid Number
- In the GeM URL format `https://bidplus.gem.gov.in/showbidDocument/<ID>`, `<ID>` is an arbitrary internal database auto-increment sequence generated at document upload time.
- In legacy seed data, the trailing numbers of public bid numbers (e.g. `8219903` from `GEM/2026/B/8219903`) were assumed to be the document ID.
- In reality, document `8219903` on GeM belonged to a 2025 battery terminal procurement for Gujarat State Road Transport Corporation.

### Bug 2: Missing Bid Number Identity Check in PDF Parser
- When `pdf_synchronizer.py` downloaded document `8219903`, it parsed the text but failed to compare the Page 1 Bid Number against `bid.bid_number`.
- It did not detect that `GEM/2025/B/6568333` != `GEM/2026/B/8219903`.

### Bug 3: Hardcoded Verification Fallback in Seeder
- In `backend/app/seeder.py`, line 100:
  ```python
  existing.target_location_status = b.get("target_location_status") or loc.target_status or "VERIFIED_BENGALURU_URBAN"
  ```
  If `b.get("target_location_status")` was missing or unresolved, the code silently injected `"VERIFIED_BENGALURU_URBAN"`.

### Bug 4: Bid Number Fallback Masking Missing PDF Evidence
- In `backend/app/seeder.py`, line 115 and line 175:
  ```python
  existing.pdf_bid_number = b.get("pdf_bid_number") or b["bid_number"]
  ```
  If no Bid Number had been extracted from the PDF, the code assumed the PDF contained the registered Bid Number, fabricating an artificial document match.

### Bug 5: Blind Alert Generation
- During application startup, `seeder.py` created alerts for matching keywords without checking whether the bid's location was genuinely verified in Bengaluru Urban.

---

## 3. Corrective Architecture & Implementation

### 3.1 Strict Fail-Closed Verification Engine (`pdf_synchronizer.py`)
1. **Header Identification:** Page 1 is parsed with strict regex for `Bid Number: (GEM/\d{4}/[A-Z]/\d+)`.
2. **Identity Verification:** `clean_pdf_bid == clean_expected_bid`.
   - If Bid Number does not match:
     - If year differs (e.g., 2025 vs. 2026): assigns `DOCUMENT_VERSION_MISMATCH`.
     - Otherwise: assigns `PDF_BID_MISMATCH`.
   - Halts delivery address assignment, sets `target_location_status = "AMBIGUOUS"`, and writes a detailed audit entry in `verification_reason`.
3. **Location Boundary Enforcement:** Even if the Bid ID matches, if the delivery state in the PDF is outside Karnataka or in a rural district, assigns `LOCATION_MISMATCH` and `OUTSIDE_TARGET`.

### 3.2 Removal of All Hardcoded Fallbacks (`seeder.py`)
- Removed all `or "VERIFIED_BENGALURU_URBAN"` instances.
- Replaced with strict `or "UNKNOWN"`.
- Removed `or b["bid_number"]` fallback on `pdf_bid_number`.

### 3.3 Quarantine and Alert Purge
- Any alert associated with a bid in `PDF_BID_MISMATCH`, `LOCATION_MISMATCH`, `DOCUMENT_VERSION_MISMATCH`, `OCR_UNCERTAIN`, `SOURCE_UNAVAILABLE`, or `OUTSIDE_TARGET` is automatically deleted on startup.
- Only bids with `synchronization_status == "VERIFIED"` and `target_location_status in ("VERIFIED_BENGALURU_URBAN", "VERIFIED_BENGALURU_CITY")` can generate alerts.

### 3.4 API Query Segregation (`bids.py`)
- The `/bids/?scope=verified` query enforces:
  - `Bid.target_location_status.in_([STATUS_VERIFIED_BENGALURU_URBAN, STATUS_VERIFIED_BENGALURU_CITY])`
  - `Bid.synchronization_status.not_in(["PDF_BID_MISMATCH", "LOCATION_MISMATCH", "DATE_MISMATCH", "DOCUMENT_VERSION_MISMATCH", "DATA_MISMATCH", "OCR_UNCERTAIN", "SOURCE_UNAVAILABLE"])`
  - `Bid.pdf_verification_status.not_in(["PDF_BID_MISMATCH", "LOCATION_MISMATCH", "DATE_MISMATCH", "DOCUMENT_VERSION_MISMATCH", "DATA_MISMATCH", "OCR_UNCERTAIN", "SOURCE_UNAVAILABLE"])`
- Quarantined bids automatically route to `/bids/?scope=review`.
