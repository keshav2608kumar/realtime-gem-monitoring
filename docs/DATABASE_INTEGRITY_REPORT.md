# GeM BidWatch — Database Schema & Data Integrity Report
**Database Engines Supported:** SQLite (Development/Render default) & PostgreSQL (Production)  
**Date:** 09 November 2026  

---

## 1. Schema & Constraints Audit

The database schema (`backend/app/models/bid.py`, `alert.py`, `profile.py`, `health.py`) implements strict relational integrity:

1. **Unique Deduplication Index:**
   - `gem_bid_id` (Unique Integer index).
   - `bid_number` (Unique String index, format `GEM/YYYY/B/XXXXXXX`).
   - Prevents duplicate rows when the scanner processes overlapping pages or repeated cycles.
2. **Batch Ingestion Idempotence:**
   - Endpoint `POST /bids/batch-sync` executes atomic transactions (`Session.commit()` with `Session.rollback()` on exception).
   - Updates mutable lifecycle fields (`end_date`, `status`, `corrigendum_status`) without overwriting historical audit metadata or first-seen timestamps.
3. **Audit Trail & Evidence Fields:**
   - `first_seen_at`: Immutable timestamp of initial tender discovery.
   - `original_pdf_checksum`: SHA-256 hash ensuring document immutability.
   - `location_verification_status`: Record of validation logic decision.
   - `synchronization_status`: Status history (`VERIFIED`, `PDF_BID_MISMATCH`, etc.).
4. **Foreign Key Integrity:**
   - `alerts.bid_id` → `bids.id` (Cascading delete protection).
   - `alerts.profile_id` → `profiles.id`.

---

## 2. Purge & Sanitation Log
- All legacy synthetic placeholder tenders (`GEM/2026/B/8219901` through `8219903`, `8095785`, etc.) were purged from the startup baseline and database tables.
- Only genuinely verified tenders extracted from official GeM portal listings and backed by authentic documents remain.
