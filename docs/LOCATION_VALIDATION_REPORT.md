# GeM BidWatch — Complete Bengaluru Region Validation Report
**Module:** `backend/app/services/location_normalizer.py`  
**Date:** 09 November 2026  

---

## 1. Target Scope Definition

Per the updated system requirements, the target area consists of the **Complete Bengaluru Region**:
1. **Bengaluru Urban District (Bangalore Urban)**
2. **Bengaluru Rural District (Bangalore Rural)**
3. **Bengaluru City (Bangalore City)**

Both districts and all verified city aliases are valid target locations. Legitimate tenders across both districts are admitted into the `Verified Bids` feed.

---

## 2. Location Acceptance Rules Matrix

| Delivery Location Observed | Classification | System Action | Target Lifecycle Status |
|---|---|---|---|
| **Bengaluru Urban District** | Accepted | Admitted to Verified Bids | `STATUS_VERIFIED_BENGALURU_URBAN` |
| **Bangalore Urban District** | Accepted | Admitted to Verified Bids | `STATUS_VERIFIED_BENGALURU_URBAN` |
| **Bengaluru Rural District** | Accepted | Admitted to Verified Bids | `STATUS_VERIFIED_BENGALURU_RURAL` |
| **Bangalore Rural District** | Accepted | Admitted to Verified Bids | `STATUS_VERIFIED_BENGALURU_RURAL` |
| **Bengaluru City** (verified KA) | Accepted | Admitted to Verified Bids | `STATUS_VERIFIED_BENGALURU_CITY` |
| **Bangalore City** (verified KA) | Accepted | Admitted to Verified Bids | `STATUS_VERIFIED_BENGALURU_CITY` |
| **Nelamangala / Doddaballapura** | Accepted | Admitted (Bengaluru Rural) | `STATUS_VERIFIED_BENGALURU_RURAL` |
| **Devanahalli / Hoskote** | Accepted | Admitted (Bengaluru Rural) | `STATUS_VERIFIED_BENGALURU_RURAL` |
| **PIN 560001 - 560110** | Accepted | Admitted (Bengaluru Urban) | `STATUS_VERIFIED_BENGALURU_URBAN` |
| **PIN 561000 - 562999** | Accepted | Admitted (Bengaluru Rural) | `STATUS_VERIFIED_BENGALURU_RURAL` |
| **Mysuru, Hubli, Dharwad, Mangaluru** | **Rejected** | Excluded from Feed | `STATUS_OUTSIDE_TARGET` |
| **Jodhpur, Dehradun, Patna, Gujarat** | **Rejected** | Excluded from Feed | `STATUS_OUTSIDE_TARGET` |
| **Ambiguous Bangalore (no district/state)**| **Review** | Routed to Review Queue | `STATUS_PARTIALLY_VERIFIED` |
| **Missing Delivery Address** | **Unknown** | Routed to Review Queue | `STATUS_UNKNOWN` |

---

## 3. Buyer vs. Consignee Delivery Decoupling
- **Rule:** The delivery location extracted from the official PDF table or structured consignee record takes absolute precedence over the buyer's administrative office.
- **Example 1:** Buyer Office: Bengaluru, Delivery Location: Jodhpur → **REJECTED (`STATUS_OUTSIDE_TARGET`)**.
- **Example 2:** Buyer Office: Jodhpur / New Delhi HQ, Delivery Location: Nelamangala (Bengaluru Rural) → **ACCEPTED (`STATUS_VERIFIED_BENGALURU_RURAL`)**.
