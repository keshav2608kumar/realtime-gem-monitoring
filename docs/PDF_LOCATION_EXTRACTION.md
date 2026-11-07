# PDF Delivery Location Extraction Engine — GeM BidWatch

## Overview
This document specifies the architecture, page prioritization strategy, text parsing logic, checksum caching, and fallback handling for extracting delivery/consignee locations from GeM bid PDF documents in **GeM BidWatch**.

---

## 1. Problem Statement & Objectives
GeM listing feeds often report only high-level buyer departments or ministry headquarters (e.g., "Ministry of Defence, New Delhi" or "Indian Railways"), while the actual consignment is delivered to a military station in Jodhpur, an ISRO center in Bangalore, or a hospital in Rishikesh. 

The authoritative delivery location is explicitly recorded in the official bid PDF document, specifically within the **"Consignees/Reporting Officer and Quantity"** section located on the final pages.

---

## 2. Technical Architecture (`pdf_location_extractor.py`)

### Processing Flow:
```
Official Bid Document Link (https://bidplus.gem.gov.in/showbidDocument/{bid_id})
                           │
                           ▼
                  [Download / Cache Check]
             (SHA-256 Checksum vs pdf_doc_hash)
                           │
                           ▼
                [pypdf Page Count Query]
               Total Pages = N (e.g. 10)
                           │
                           ▼
              [Prioritize Final Pages First]
          Pages: [N-1, N-2, N-3] ➔ [N-4 ... 0]
                           │
                           ▼
              [Digital Text Extraction]
               (pypdf.Page.extract_text)
                           │
                           ▼
               [Regex Section Detection]
         "Consignees/Reporting Officer and Quantity"
                           │
                           ▼
          [Structured Location & PIN Parser]
    - Consignee Name / Designation
    - Organization / Military Unit
    - Street / Locality
    - Village / City / Town
    - District & State
    - 6-Digit Indian PIN Code (Postal Zone Verified)
                           │
                           ▼
          [Confidence Scoring & Verification]
             (VERIFIED / PARTIALLY_VERIFIED)
                           │
                           ▼
                 [Database Persistence]
```

---

## 3. Page Prioritization Strategy
GeM tender documents place general specifications and BOQ items in pages 1 through N-3. The consignee and delivery location details reside in the final 1 to 3 pages.

### Scanning Order:
1. `page = total_pages - 1` (Final page)
2. `page = total_pages - 2` (Penultimate page)
3. `page = total_pages - 3` (3rd from last)
4. If a high-confidence `VERIFIED` record is found in these final pages, the scanner terminates immediately without processing earlier pages, saving CPU and memory.
5. If not found in the last 3 pages, scanning proceeds backwards towards page 0.

---

## 4. Structured Data Fields Extracted

Every extraction produces an `ExtractedDeliveryLocation` record with the following fields:

| Field Name | Type | Description | Example Value |
|---|---|---|---|
| `consignee_name` | String | Reporting officer name or designation | `"Col. Rajesh Sharma"` / `"Stores Officer"` |
| `organization` | String | Procuring establishment / campus | `"Headquarters South Western Command"` |
| `building_campus`| String | Specific facility or station | `"Military Station"` |
| `street_locality`| String | Local street, road, or area | `"Virbhadra Road"` |
| `city` | String | City or village | `"Jodhpur"` / `"Bangalore"` |
| `district` | String | Administrative district | `"Jodhpur"` / `"Bangalore Urban"` |
| `state` | String | Canonical Indian State / UT | `"RAJASTHAN"` / `"KARNATAKA"` |
| `pincode` | String | 6-digit Postal Index Number | `"342005"` / `"560017"` |
| `full_address` | Text | Complete original address string | `"342005, Headquarters South Western Command, Military Station, Jodhpur, Rajasthan"` |
| `page_number` | Integer | 1-indexed PDF page where found | `8` (out of 8) |
| `total_pages` | Integer | Total page count of document | `8` |
| `extraction_method`| String | `PDF_TEXT` or `OCR` | `"PDF_TEXT"` |
| `confidence_score`| Float | Score between 0.0 and 1.0 | `0.95` |
| `verification_status`| String | Lifecycle status | `VERIFIED` |
| `doc_hash` | String | SHA-256 checksum of document bytes | `"a1b2c3..."` |

---

## 5. Checksum Caching & Redundancy Prevention
Before downloading or parsing, documents are hashed using SHA-256. If a bid already has an identical `pdf_doc_hash` and `pdf_verification_status == 'VERIFIED'`, the extractor skips re-processing, avoiding redundant network traffic and compute load.

---

## 6. On-Demand & Background Execution
- **Background Worker**: Bids ingested via `/bids/batch-sync` can be enriched asynchronously.
- **On-Demand API Trigger**: Users can trigger or re-verify extraction for any bid using:
  ```http
  POST /bids/{bid_id}/extract-pdf
  ```
  Returns the updated `BidOut` schema with all delivery fields populated.

---

## 7. Frontend Modal & Feed Display
- In the dashboard table, verified bids display a distinct green badge:
  `<i class="fa-solid fa-file-circle-check text-emerald-400"></i> Jodhpur, RAJASTHAN (PIN: 342005)`
- Clicking **Details** opens the **Tender Intelligence & PDF Delivery Address Modal**:
  - Displays the full extracted address, consignee designation, organization, PIN code, and page number.
  - If unextracted, displays: *"Delivery address could not be verified from the available document."* with an interactive **"Extract / Re-verify from PDF"** action button.
