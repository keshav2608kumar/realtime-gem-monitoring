# GeM BidWatch — PDF Document Synchronization Report

**Document Date:** 2026-11-07  
**Module:** `app.services.pdf_synchronizer`, `app.services.pdf_location_extractor`  
**Classification:** P0 Critical System Engineering & Document Provenance

---

## 1. Objectives & Overview

Official GeM procurement notices publish definitive contractual terms, quantities, line items, and delivery schedules in PDF documents (`https://bidplus.gem.gov.in/showbidDocument/{bid_id}`). In past iterations, external scraping and loose matching suffered from:
1. Missing bidirectional document verification (no validation that the PDF contained the exact expected `bid_number`).
2. Redundant re-processing of unchanged documents.
3. Absence of segregated document provenance fields (overwriting source values with normalized/inferred data).
4. Unhandled corrigendum date extensions.

To achieve strict document integrity, we engineered the **10-Step Document-to-Bid Synchronization Protocol** in `app.services.pdf_synchronizer`.

---

## 2. The 10-Step Document-to-Bid Synchronization Protocol

1. **Official Record Retrieval:** Fetch database bid record and locate the authoritative GeM document URL (`bid_url`).
2. **Document Retrieval & SHA-256 Checksum:** Download raw PDF bytes and generate a 64-character SHA-256 hash (`original_pdf_checksum`).
3. **Checksum Caching:** If the document checksum matches the previously recorded hash and the record is already `SYNCHRONIZED`, bypass expensive PDF parsing unless forced.
4. **Header & Metadata Extraction (Page 1):**
   - Extract Bid Number (`Bid Number: GEM/2026/B/...`)
   - Extract Publication Date (`Dated: DD-MM-YYYY`)
   - Extract Bid Closing Deadline (`Bid End Date/Time: DD-MM-YYYY HH:MM:SS`)
   - Extract Official Item Category (`Item Category: ...`)
   - Extract Ministry, Department, and Office names.
5. **Bid Number Cross-Verification:**
   - Compare `pdf_bid_number` with `bid.bid_number`.
   - If mismatch is detected (e.g. PDF contains `GEM/2026/B/9999999` while bid record is `GEM/2026/B/8123875`), immediately flag as `DATA_MISMATCH`.
   - Quarantines the mismatched record into the `Review Queue` and prevents it from entering the `Verified Bids` feed.
6. **Consignee & Delivery Location Extraction:**
   - Scan document prioritizing the final pages (penultimate, last pages) where the *'Consignees/Reporting Officer and Quantity'* table is situated.
   - Extract Recipient, Organization, Address, City, District, State, and PIN code.
7. **Corrigenda & Deadline Evaluation:**
   - Retrieve applicable corrigenda in chronological sequence.
   - Determine `latest_revised_deadline` and record corrigendum reference notes.
   - If a corrigendum revised deadline is in the future, maintain `ACTIVE` status even if the original deadline has lapsed.
   - Never overwrite `original_end_date`.
8. **Administrative Target Location Classification:**
   - Evaluate extracted delivery details against strict geographic criteria:
     - `STATUS_VERIFIED_BENGALURU_URBAN` (e.g. Bangalore Urban, PIN 560001–560110)
     - `STATUS_VERIFIED_BENGALURU_CITY` (e.g. Bangalore City, Karnataka)
     - `STATUS_OUTSIDE_TARGET` (e.g. Bengaluru Rural, Jodhpur, Dehradun, Patna)
     - `STATUS_AMBIGUOUS` (routed to Review Queue)
9. **Confidence & Lifecycle Scoring:**
   - Compute data confidence score based on verified PIN code postal matching and definitive administrative terms.
   - Determine lifecycle status: `ACTIVE`, `CLOSING_SOON`, `EXPIRED`, `CANCELLED`, or `DATA_MISMATCH`.
10. **Idempotent Atomic Persistence:**
    - Persist all 20+ provenance and audit fields into separate database columns within a single database transaction.

---

## 3. Dedicated Provenance & Audit Fields

All data points are stored in distinct, dedicated columns:

| Database Column | Data Type | Purpose & Verification Rule |
|---|---|---|
| `official_source_url` | VARCHAR(500) | Primary GeM web portal link |
| `original_pdf_url` | VARCHAR(500) | Direct document download URL |
| `original_pdf_checksum` | VARCHAR(64) | SHA-256 hash of document binary |
| `document_version` | VARCHAR(50) | Version indicator (e.g. 1.0, Corrigendum No. 1) |
| `original_publication_date` | TIMESTAMP | Publication date extracted from Page 1 |
| `original_end_date` | TIMESTAMP | Initial closing deadline extracted from Page 1 |
| `revised_end_date` | TIMESTAMP | Revised closing deadline from official corrigendum |
| `corrigendum_reference` | VARCHAR(200) | Corrigendum number and reference description |
| `corrigendum_date` | TIMESTAMP | Date of corrigendum publication |
| `latest_verified_status` | VARCHAR(50) | Current lifecycle status (`ACTIVE`, `EXPIRED`, etc.) |
| `raw_extracted_text` | TEXT | First 2000 chars of extracted document text |
| `extracted_category` | TEXT | Official category extracted from Page 1 |
| `extracted_consignee_name`| VARCHAR(200) | Consignee/Reporting officer designation |
| `extracted_delivery_address`| TEXT | Full delivery address extracted from final pages |
| `extracted_city` | VARCHAR(100) | Delivery city |
| `extracted_district` | VARCHAR(100) | Delivery administrative district |
| `extracted_state` | VARCHAR(100) | Delivery state |
| `extracted_pincode` | VARCHAR(20) | Indian 6-digit postal code |
| `pdf_bid_number` | VARCHAR(100) | Bid number parsed from document Page 1 |
| `pdf_details_page_number` | INTEGER | Page number of header metadata (Page 1) |
| `pdf_page_number` | INTEGER | Page number where consignee address was found |
| `extraction_timestamp` | TIMESTAMP | UTC timestamp of text extraction |
| `verification_timestamp` | TIMESTAMP | UTC timestamp of verification evaluation |
| `data_confidence` | FLOAT | Numeric confidence score (0.00 – 1.00) |
| `synchronization_status` | VARCHAR(50) | `SYNCHRONIZED`, `DATA_MISMATCH`, `FAILED`, `PDF_UNAVAILABLE` |

---

## 4. Test Verification Evidence

| Scenario | Input / Test Case | Expected Result | Actual Result | Status |
|---|---|---|---|---|
| Matching Bid & PDF | `GEM/2026/B/8123875` with `test_gem_9993172.pdf` | `is_bid_matched=True`, `SYNCHRONIZED` | Extracted Page 1 Bid No `GEM/2026/B/8123875`, Page 3 Bangalore Urban | **PASS** |
| Mismatched Bid & PDF | `GEM/2026/B/9999999` with `test_gem_9993172.pdf` | `is_bid_matched=False`, `DATA_MISMATCH` | Quarantined to Review Queue; excluded from Verified Bids | **PASS** |
| Missing PDF Document | Bid record with null/empty URL | `synchronization_status=PDF_UNAVAILABLE` | Clean error handled; no fabricated values generated | **PASS** |
| Corrupted PDF File | Truncated/garbage PDF stream | `synchronization_status=FAILED` | Gracefully captured; no server crash | **PASS** |
| Checksum Caching | Re-syncing same binary bytes | Skip repeated OCR/text extraction | Matched existing hash; instant return | **PASS** |
| Checksum Invalidation | Modified bytes / new revision | Trigger re-verification | Computed new SHA-256; re-extracted fields | **PASS** |
| Corrigendum Extension | Past original date + Future revised date | `bid_status=ACTIVE` | Evaluated against `revised_end_date`; marked ACTIVE | **PASS** |
