# GeM BidWatch — Data Mapping & Provenance Specification

This document defines the exact field mappings between Government e-Marketplace (GeM) source payloads and the internal `Bid` data model, preserving raw provenance and enforcing strict data accuracy.

---

## 1. GeM API to Database Model Mapping

| GeM Source Field | Type in GeM | Database Column (`bids`) | Normalized Type | Description & Handling |
| :--- | :--- | :--- | :--- | :--- |
| `b_id` | Integer / List | `gem_bid_id` | `Integer` (Unique, Indexed) | Unique GeM tender ID. Essential field. |
| `b_bid_number` | String / List | `bid_number` | `String(100)` (Unique) | Official tender identifier (e.g. `GEM/2026/B/8123875`). |
| `b_bid_number_parent` | String / List | `bid_number_parent` | `String(100)` | Parent tender ID in case of Reverse Auction (RA). |
| `b_category_name` | String / List | `category_name` | `Text` | Full item / product category description. |
| `b_total_quantity` | Integer / List | `quantity` | `Integer` | Total items requested by the buyer. |
| `b_bid_type` | Integer / List | `bid_type` | `Integer` | 1 = Standard Bid, 2 = Reverse Auction (RA), 5 = Direct RA. |
| `b_status` | Integer / List | `status` | `Integer` | GeM status code (0 = Draft, 1 = Active, 2 = Cancelled, 3 = Completed). |
| `is_high_value` | Boolean / List | `is_high_value` | `Boolean` | Flag indicating high-value procurement. |
| `b_estimated_value` | Float / List | `estimated_value` | `Float` | Estimated tender monetary value in INR, if published. |
| `ba_official_details_deptName` | String / List | `dept_name` | `String(255)` | Procuring Department (e.g. `ISRO Satellite Centre`). |
| `ba_official_details_minName` | String / List | `ministry_name` | `String(255)` | Procuring Ministry (e.g. `Department of Space`). |
| `final_start_date_sort` | ISO String | `start_date` | `DateTime(UTC)` | Official publication / tender start date. |
| `final_end_date_sort` | ISO String | `end_date` | `DateTime(UTC)` | Official closing deadline. |
| *Calculated* | — | `bid_status` | `String(50)` | Lifecycle: `ACTIVE`, `CLOSING_SOON`, `EXPIRING_TODAY`, `EXPIRED`. |
| *Calculated* | — | `consignee_state` | `String(100)` | Administrative State from verified location lookup. |
| *Calculated* | — | `consignee_district`| `String(100)` | Administrative District from verified location lookup. |
| *Calculated* | — | `consignee_city` | `String(100)` | Administrative City from verified location lookup. |
| `b_cat_id` | String / List | `cat_id` | `String(200)` | GeM category identifier. |
| *Document URL* | — | `bid_url` | `String(500)` | Official GeM PDF URL (`https://bidplus.gem.gov.in/showbidDocument/{id}`). |
| *Raw Payload* | JSON Dict | `raw_source_record` | `Text` | Complete unaltered JSON received from GeM. |
| *System Clock* | — | `source_retrieval_time` | `DateTime(UTC)` | Exact timestamp when scanner fetched the payload. |
| *System Clock* | — | `first_seen_at` | `DateTime(UTC)` | Timestamp when record was first persisted in database. |

---

## 2. Data Provenance & Classifications

Every tender record in GeM BidWatch carries a `data_source_classification`:

1. **`LIVE_VERIFIED`**:
   - Ingested directly from GeM portal live AJAX APIs (`search-bids` or `all-bids-data`).
   - Retains unaltered `raw_source_record`.
   - Verified location confidence: `VERIFIED` or `NORMALIZED`.
2. **`IMPORTED`**:
   - Ingested from verified baseline historical datasets (`baseline_bids.json`).
   - Represents genuine past or curated tenders.
   - Distinctly labeled in the UI so users know it is imported historical data.
3. **`SIMULATED`**:
   - Used only in offline test suites or synthetic mock environments.
   - Never stored in production database without explicit test prefix.

---

## 3. Strict Non-Fabrication Rules

1. **Missing Location:**
   - If a source payload lacks state or city and cannot be resolved through department text, `consignee_city` and `consignee_state` remain `NULL`.
   - `location_verification_status` is marked `UNKNOWN`.
   - Frontend displays: `"Not available from source"`.
   - **Never default to Bangalore or any other city.**
2. **Missing Publication Date:**
   - If `final_start_date_sort` is missing, `start_date` remains `NULL`.
   - Frontend displays: `"Not available from source"`.
   - **Never default to current time or ingestion time.**
3. **Missing Closing Deadline:**
   - If `final_end_date_sort` is missing, `end_date` remains `NULL`.
   - `bid_status` is set to `UNKNOWN`.
   - Frontend displays: `"Not available from source"`.
   - **Never default to a fixed placeholder date.**
