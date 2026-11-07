# GeM BidWatch — QA Initial Audit Report

**Date:** 2026-11-07  
**Auditor:** Senior QA & Systems Engineering Team  
**Scope:** Complete Codebase, Ingestion, PDF Processing Pipeline, Location Segregation, Corrigenda, Expiry Tracking, Database Architecture, and Dashboard

---

## 1. Executive Summary

This comprehensive audit of the **GeM BidWatch** system investigates the end-to-end data processing lifecycle from official GeM portal ingestion, PDF retrieval and structural parsing, corrigendum resolution, administrative boundary verification (Bengaluru Urban & Bengaluru City), database persistence, to frontend presentation and alerts.

While earlier releases established basic API scraping, database schemas, and baseline seeding, this audit identifies critical synchronization vulnerabilities between official GeM PDF documents and database records, lack of bid number cross-verification within PDF content, gaps in document provenance fields, and potential date/corrigendum race conditions.

---

## 2. Detailed Issue Registry

### Issue 1: Bid Number Verification Inside PDF Document Missing (P0 - CRITICAL)
- **Severity:** P0 (Critical)
- **Component:** `app.services.pdf_location_extractor` & `app.routers.bids`
- **Root Cause:** The existing PDF parser (`extract_location_from_pdf`) only inspects the final pages for consignee tables and extracts address lines. It does not extract the `Bid Number` or `Dated` fields from Page 1 of the official GeM document, nor does it verify that the document actually matches the database bid record (`bid.bid_number`).
- **Risk:** If a corrupted, mismatched, or misplaced PDF URL is associated with a bid, the system would extract an arbitrary consignee address and mark the bid as `VERIFIED`, leading to false positive locations or attaching wrong delivery details.
- **Proposed Correction:**
  1. Build an enhanced document synchronization engine that parses Page 1 of the PDF.
  2. Extract `Bid Number` (e.g. `GEM/2026/B/8123875`), `Dated` (publication date), `Bid End Date/Time`, and `Item Category`.
  3. Perform bidirectional validation: `pdf_bid_number == bid.bid_number`.
  4. If `pdf_bid_number` does not match, set `synchronization_status = 'DATA_MISMATCH'`, flag error details, and route the record to the `Review Queue` instead of `Verified Bids`.

---

### Issue 2: Missing Granular Document Provenance and Synchronization Fields (P0 - CRITICAL)
- **Severity:** P0 (Critical)
- **Component:** `app.models.bid`, `app.schemas`, `app.database`
- **Root Cause:** While the `bids` table has fields for `pdf_doc_hash` and `pdf_delivery_address`, it lacks separate persistent columns for:
  - `official_source_url`
  - `original_pdf_url`
  - `original_pdf_checksum`
  - `document_version`
  - `original_publication_date`
  - `original_deadline`
  - `latest_revised_deadline`
  - `corrigendum_reference` & `corrigendum_date`
  - `latest_verified_status`
  - `raw_extracted_text`
  - `extracted_category`
  - `extracted_consignee_name`
  - `extracted_delivery_address`
  - `extracted_city` & `extracted_district`
  - `extraction_timestamp` & `verification_timestamp`
  - `data_confidence`
  - `synchronization_status`
- **Risk:** Overwriting original source data with normalized/inferred data makes audits impossible, obscures data lineage, and violates compliance requirements.
- **Proposed Correction:**
  1. Add dedicated columns to the `bids` table with automated SQLite migration in `database.py`.
  2. Never overwrite original source values with normalized or inferred values; store them in separate extracted and normalized columns.

---

### Issue 3: Corrigendum Chronology & Deadlines Resolution (P1 - HIGH)
- **Severity:** P1 (High)
- **Component:** `app.services.bid_status_service`, `app.routers.bids`
- **Root Cause:** Some bids experience multiple corrigenda extending the deadline from an expired date to a future date. If the system only tracks `original_end_date` or fails to order corrigenda chronologically, an active bid could be marked as `EXPIRED` or an expired bid could remain `ACTIVE`.
- **Risk:** Missed tender opportunities due to premature expiration, or bids displayed as active after their deadline has elapsed.
- **Proposed Correction:**
  1. Implement explicit deadline hierarchy:
     - If valid corrigendum exists with revised deadline: `end_date = revised_end_date`.
     - Else: `end_date = original_end_date`.
  2. Evaluate status dynamically using `datetime.now(timezone.utc)` against `Asia/Kolkata` time.
  3. Categorize statuses strictly: `ACTIVE`, `CLOSING_SOON`, `EXPIRED`, `CANCELLED`, `DATA_MISMATCH`, `UNKNOWN`.
  4. Never display an expired bid as active.

---

### Issue 4: Location Verification Scoping (Bengaluru City & Bengaluru Urban District) (P1 - HIGH)
- **Severity:** P1 (High)
- **Component:** `app.services.location_normalizer`, `app.routers.bids`
- **Root Cause:** Previous iterations of the dashboard occasionally conflated Buyer Office location with Delivery/Consignee location, or allowed Bengaluru Rural or other districts (e.g. Jodhpur, Dehradun) to leak into verified feeds.
- **Risk:** Contractors bidding on tenders expecting delivery in Bangalore when delivery is actually in Jodhpur or Bengaluru Rural.
- **Proposed Correction:**
  1. Enforce strict 3-tier delivery location priority:
     - Priority 1: Verified PDF consignee/delivery address.
     - Priority 2: Structured GeM delivery/consignee location.
     - Priority 3: Explicit consignee evidence.
  2. Buyer location alone must NEVER determine delivery location.
  3. Explicitly reject: Bengaluru Rural, Jodhpur, Dehradun, Patna, and all other non-target districts.
  4. Only accept `STATUS_VERIFIED_BENGALURU_URBAN` and `STATUS_VERIFIED_BENGALURU_CITY` into `Verified Bids`.
  5. Route ambiguous records to the `Review Queue`.

---

### Issue 5: Seven Product Category Filter Consistency (P1 - HIGH)
- **Severity:** P1 (High)
- **Component:** `app.services.category_service`, `app.gem.filter_matcher`, `app.routers.bids`
- **Root Cause:** Category filters must support the 7 required categories both independently and in multi-select combinations, with exact string matching and canonical alias mappings.
- **Risk:** Filtering by one or more categories could inadvertently omit matching bids or return unmapped items if category keys are not normalized.
- **Proposed Correction:**
  1. Verify canonical category keys:
     - `TONER_INK_PRINTER_CONSUMABLES`
     - `SCANNER_V3`
     - `A4_LEGAL_MFP`
     - `A3_MFP`
     - `COMPUTER_PRINTER_V2`
     - `HIGH_END_DESKTOP`
     - `HIGH_END_LAPTOP`
  2. Ensure SQL queries in `routers/bids.py` handle multiple category IDs via `IN (...)` filtering with exact match support.

---

### Issue 6: Alarm Feature Artifacts & Dashboard Navigation (P2 - MEDIUM)
- **Severity:** P2 (Medium)
- **Component:** `app.dashboard`, `app.static`
- **Root Cause:** Audio playback, siren buttons, and redundant tabs (`Closing Soon`, `Expired Archive`, `All Ingested Records`) cluttered the interface.
- **Risk:** User frustration, audio permission prompts, noisy UI, and fragmented navigation.
- **Proposed Correction:**
  1. Consolidate navigation to ONLY TWO main tabs: `Verified Bids` and `Review Queue`.
  2. Compact status dropdown: `All Active`, `Closing Soon (<24h)`, `Expired`, `Cancelled`.
  3. Completely eliminate alarm audio, buttons, and settings while keeping visual alerts and notification history intact.

---

### Issue 7: Alert Counters vs Notification Delivery (P2 - MEDIUM)
- **Severity:** P2 (Medium)
- **Component:** `app.models.alert`, `app.routers.alerts`
- **Root Cause:** Fired alerts (database match records) were sometimes reported as delivered push notifications, leading to count discrepancies if delivery failed or tokens were missing.
- **Risk:** Metric confusion between discovered tender matches and transmitted device notifications.
- **Proposed Correction:**
  1. Maintain separate counters: `total_alerts` (fired matches) and `notifications_sent` (delivered push notifications).
  2. Enforce unique constraint `(profile_id, bid_id)` to prevent duplicate alert records.

---

## 3. Implementation Roadmap

1. **Database Schema Upgrade**:
   - Add all 20 document-to-bid synchronization and provenance columns to `Bid`.
   - Update `database.py` with automatic SQLite migration.
2. **Enhanced PDF & Corrigendum Synchronization Engine**:
   - Build `pdf_synchronizer.py` implementing bidirectional Bid Number verification, publication date extraction, deadline cross-checking, corrigendum chaining, and checksum caching.
3. **Backend API & Service Upgrades**:
   - Enhance `/bids/` and `/bids/{id}/extract-pdf` to execute full document synchronization, check checksum changes, and flag `DATA_MISMATCH`.
4. **End-to-End Automated Testing**:
   - Build a comprehensive test suite in `tests/` covering all mandatory scenarios (PDF match/mismatch, checksum, location, categories, dates, errors).
5. **Documentation Deliverables**:
   - Create all 8 required documentation reports in `docs/`.
6. **Deployment & Live Smoke Testing**:
   - Commit, push to `main`, verify live deployment on Render, and perform live production smoke tests.
