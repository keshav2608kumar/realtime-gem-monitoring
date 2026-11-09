# GeM BidWatch — Root Cause Analysis (RCA) Report
**Incident ID:** `RCA-2026-11-09`  
**Subjects Investigated:**
1. Why the Cloud Application was stuck on 8 bids and not updating from GeM.
2. Why PDF Bid Mismatch occurred on tender `GEM/2026/B/8219903`.
3. Why Bengaluru Rural tenders were previously rejected.

---

## 1. Cloud Ingestion Stoppage (Render Singapore vs GeM Firewall)

### Symptoms
- The live Render application (`https://realtime-gem-monitoring.onrender.com/`) showed 8 initial baseline tenders for days without ingesting fresh bids.
- Polling logs showed `last_check: null` or `403 Forbidden` / `Connection refused`.

### Technical Root Cause
- The production Web Service is deployed on Render in Singapore (`region: singapore` in `render.yaml`).
- The Government e-Marketplace (`bidplus.gem.gov.in`) uses an aggressive National Web Application Firewall (NIC / Cloudflare WAF).
- The WAF enforces geographic filtering: requests from foreign datacenter IP blocks (Singapore, AWS US-East, Azure Europe) are dropped at the TCP layer (`Errno 111 Connection refused`) or returned as `403 Forbidden`.
- Because Render is hosted in Singapore, its background worker (`monitor_worker.py`) could not establish a connection to GeM.

### Permanent Resolution
1. Created `cloud_scanner/` designed to run in an Indian Cloud Region (AWS Mumbai `ap-south-1`, GCP Mumbai `asia-south1`, or Fly.io `bom`).
2. Added `GEM_PROXY_URL` support in `backend/app/gem/session.py` to route through domestic egress if proxy is configured.
3. Added secure `/bids/batch-sync` API so the Indian cloud worker pushes fresh verified tenders into Render's cloud datastore.

---

## 2. PDF Bid Mismatch (`GEM/2026/B/8219903`)

### Symptoms
- On the web dashboard, row displayed:
  - Tender Number: `GEM/2026/B/8219903`
  - Published: 06 Nov 2026, Deadline: 27 Nov 2026
  - Delivery Location: Bengaluru Urban, PIN 560038
- When user clicked `[PDF]`, the downloaded document displayed:
  - Bid Number: `GEM/2025/B/6568333`
  - Dated: 13-08-2025, Deadline: 03-09-2025
  - Consignee: Gujarat

### Technical Root Cause
- In the initial prototype seeder, placeholder synthetic records were populated using dummy sequential IDs without running cryptographic byte-stream verification against the official GeM document.
- The PDF download link was constructed using a heuristic ID without verifying the text inside the downloaded PDF stream.

### Permanent Resolution
1. Built `backend/app/services/pdf_synchronizer.py` implementing **Fail-Closed Bid-to-PDF Identity Verification**.
2. Reads the first 2 pages of every downloaded PDF and extracts the Bid Number using regex `r"GEM/\d{4}/[B|R]/\d+"`.
3. If extracted PDF Bid Number != Bid Number:
   - Assigns `STATUS_PDF_BID_MISMATCH`.
   - Strips unverified delivery address and dates.
   - Quarantines the record strictly into the **Review Queue**.
   - Generates SHA-256 document checksum.
4. Purged all legacy synthetic tenders from `backend/app/baseline_bids.json` and database seeder.

---

## 3. Bengaluru Rural District Exclusion

### Symptoms
- User observed that only Bengaluru Urban tenders appeared on the dashboard, while Bangalore Rural tenders were missing.

### Technical Root Cause
- A previous version hardcoded an exclusion rule:
  ```python
  if "rural" in combined:
      return STATUS_OUTSIDE_TARGET
  ```
- This caused legitimate tenders destined for industrial clusters in Nelamangala, Doddaballapura, Devanahalli, and Hoskote to be classified as `OUTSIDE_TARGET`.

### Permanent Resolution
- Updated target definition to **Complete Bengaluru Region** (Bengaluru Urban + Bengaluru Rural + Bengaluru City).
- Created `STATUS_VERIFIED_BENGALURU_RURAL` with verified acceptance.
- Added Bengaluru Rural dropdown option and summary chips in the dashboard.
