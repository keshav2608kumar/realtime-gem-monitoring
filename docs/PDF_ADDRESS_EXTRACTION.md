# GeM Bid Document PDF Delivery Address Extraction Engine

## Overview
This document specifies the technical architecture, page prioritization strategy, table parsing regex, postal PIN code validation, checksum caching, and fallback handling for extracting delivery and consignee locations from official GeM bid PDF documents.

---

## 1. Problem Statement
GeM listing search results frequently display only the buyer ministry headquarters or central office (e.g., "Ministry of Defence, New Delhi" or "Ministry of Railways"), whereas the actual delivery point is located at an operational station in Bengaluru Urban, Jodhpur, or Dehradun. 

The authoritative delivery destination is explicitly stated in the **"Consignees/Reporting Officer and Quantity"** section of the official bid PDF document, predominantly located on the final pages.

---

## 2. Technical Architecture (`app/services/pdf_location_extractor.py`)

### Processing Pipeline:
```
Official GeM Bid PDF (https://bidplus.gem.gov.in/showbidDocument/{bid_id})
                            │
                            ▼
              [Document Checksum Validation]
       SHA-256 against cached b.pdf_doc_hash
                            │
                            ▼
                [pypdf Page Count Query]
                     Total Pages = N
                            │
                            ▼
              [Prioritize Final Pages First]
          Pages: [N-1, N-2, N-3] ➔ [N-4 ... 0]
                            │
                            ▼
                 [Digital Text Extraction]
                  pypdf.Page.extract_text()
                            │
                            ▼
              [Consignee Table Block Parser]
   Regex for "Consignees/Reporting Officer and Quantity"
                            │
                            ▼
            [Structured Field & PIN Extractor]
     - Consignee Name / Designation
     - Procuring Organization / Campus
     - Street / Locality
     - City / Town
     - Administrative District
     - Canonical State / UT
     - 6-Digit Indian Postal PIN Code
                            │
                            ▼
          [Postal PIN Range & District Verification]
      (560001 - 560110 ➔ VERIFIED_BENGALURU_URBAN)
                            │
                            ▼
                [Database Persistence]
       (pdf_delivery_address, pdf_delivery_city,
        pdf_delivery_district, pdf_delivery_state,
        pdf_delivery_pincode, pdf_page_number)
```

---

## 3. Page Prioritization Strategy
GeM tender PDFs range between 4 and 40 pages. Standard clauses, general terms, and specification tables occupy pages 1 through N-3. Consignee delivery tables reside on the final 1 to 3 pages.

### Scanning Order:
1. `page = total_pages - 1` (Final page)
2. `page = total_pages - 2` (Penultimate page)
3. `page = total_pages - 3` (3rd from last page)
4. **Early Termination:** If a high-confidence delivery block containing a verified PIN code and district is extracted from these final pages, scanning terminates immediately without parsing the remaining pages.
5. If no delivery table is detected in the last 3 pages, scanning proceeds backwards toward page 0 as a fallback.

---

## 4. Extracted Data Schema

| Field Name | Type | Description | Example Value |
|---|---|---|---|
| `consignee_name` | String | Reporting officer or designation | `"Stores Officer"` / `"Col. R. Sharma"` |
| `organization` | String | Procuring establishment / campus | `"ISRO Satellite Centre"` |
| `building_campus`| String | Facility or campus | `"URSC Campus, Old Airport Road"` |
| `street_locality`| String | Local street or road | `"Vimanapura"` |
| `city` | String | City or town | `"Bengaluru"` |
| `district` | String | Administrative district | `"Bengaluru Urban"` |
| `state` | String | Canonical State / UT | `"KARNATAKA"` |
| `pincode` | String | 6-Digit Indian Postal PIN | `"560017"` |
| `full_address` | Text | Complete raw delivery block | `"560017, ISRO Satellite Centre, Vimanapura, Bengaluru Urban, Karnataka"` |
| `page_number` | Integer | 1-indexed page where extracted | `12` |
| `total_pages` | Integer | Total pages in PDF | `12` |
| `extraction_method`| String | `PDF_TEXT` or `OCR` | `"PDF_TEXT"` |
| `confidence_score`| Float | Confidence metric (0.0 - 1.0) | `0.95` |
| `verification_status`| String | `VERIFIED`, `PARTIALLY_VERIFIED`, etc. | `"VERIFIED"` |
| `doc_hash` | String | SHA-256 hash of document bytes | `"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"` |

---

## 5. Checksum Caching
To prevent redundant network requests and compute overhead on repetitive scans:
1. Every fetched PDF is hashed via SHA-256.
2. If `b.pdf_doc_hash == current_hash` and `b.pdf_verification_status == 'VERIFIED'`, extraction is bypassed.
3. If the PDF URL changes or a re-verification is manually triggered, the cache is refreshed.

---

## 6. OCR Architecture & Scanned PDF Fallback
When digital text streams in a PDF yield fewer than 40 characters (indicative of scanned images or flat rasterization), the engine flags the document for OCR processing:
- Method: `OCR`
- Extractor interface: Tesseract OCR via `pytesseract` / native image extraction
- Preprocessing: Grayscale conversion, adaptive thresholding (Otsu's), and morphological closing
- Status: When OCR dependencies are not installed in the container environment, the status cleanly defaults to `PDF_UNAVAILABLE` or `PARTIALLY_VERIFIED` without crashing the application.
