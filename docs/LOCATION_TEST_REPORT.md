# GeM BidWatch — Location Verification Test Report

**Document Date:** 2026-11-07  
**Module:** `app.services.location_normalizer`  
**Target Scope:** Bengaluru City & Bengaluru Urban District (Karnataka, India)

---

## 1. Location Verification Priority Hierarchy

To ensure out-of-target bids from districts like Jodhpur, Dehradun, Patna, or Bengaluru Rural never enter the verified feed, location is resolved strictly in the following priority order:

1. **Priority 1: Verified Official PDF Consignee/Delivery Address**  
   Extracted from the final pages of the official GeM PDF. Requires matching administrative terms, PIN code within target range, or explicit district designation.
2. **Priority 2: Official Structured GeM Delivery Location**  
   Derived from structured `delivery_city`, `delivery_district`, `delivery_state`.
3. **Priority 3: Official Structured Consignee Location**  
   Derived from `consignee_city`, `consignee_district`, `consignee_state`.

> [!CRITICAL]
> **Buyer Office Location Rule:** Buyer office location (`buyer_state`, `buyer_district`, `buyer_city`) is **strictly excluded** from delivery location matching. A buyer located in Bangalore who orders goods for delivery in Jodhpur must be **REJECTED**. Conversely, a buyer located in Jodhpur who orders goods for delivery to Bengaluru Urban must be **ACCEPTED**.

---

## 2. Supported Target Locations & Aliases

The system actively supports two legitimate target locations within Karnataka:

1. **Bengaluru Urban District:**
   - Canonical: `Bengaluru Urban`
   - Aliases: `Bangalore Urban`, `Bangalore Urban District`, `Bengaluru Urban, Karnataka`
   - PIN Code Range: `560001` to `560110`
   - Classification Status: `STATUS_VERIFIED_BENGALURU_URBAN`

2. **Bengaluru City:**
   - Canonical: `Bengaluru City`
   - Aliases: `Bengaluru`, `Bangalore`, `Bangalore City`, `Bengaluru, Karnataka`
   - Classification Status: `STATUS_VERIFIED_BENGALURU_CITY`

---

## 3. Strict Rejection Boundaries

The following locations are strictly rejected:
- **Bengaluru Rural District:** (Nelamangala, Doddaballapura, Devanahalli, Hosakote) -> `STATUS_OUTSIDE_TARGET`
- **Other Karnataka Districts:** (Mysore, Mangalore, Hubli, Belgaum, Dharwad) -> `STATUS_OUTSIDE_TARGET`
- **Other Indian States & Districts:**
  - Jodhpur, Jaipur, Rajasthan -> `STATUS_OUTSIDE_TARGET`
  - Dehradun, Haridwar, Uttarakhand -> `STATUS_OUTSIDE_TARGET`
  - Patna, Gaya, Bihar -> `STATUS_OUTSIDE_TARGET`
  - Delhi, Mumbai, Kolkata, Chennai -> `STATUS_OUTSIDE_TARGET`

---

## 4. Test Results Matrix

| Test Scenario | Input Data | Target Status | Feed Destination | Result |
|---|---|---|---|---|
| Bengaluru Urban District | City: "Bengaluru", District: "Bengaluru Urban", State: "KARNATAKA" | `STATUS_VERIFIED_BENGALURU_URBAN` | Verified Bids | **PASS** |
| Bangalore Urban District | City: "Bangalore", District: "Bangalore Urban", PIN: "560094" | `STATUS_VERIFIED_BENGALURU_URBAN` | Verified Bids | **PASS** |
| Bengaluru City | City: "Bengaluru", State: "KARNATAKA" | `STATUS_VERIFIED_BENGALURU_CITY` | Verified Bids | **PASS** |
| Bangalore City | City: "Bangalore", State: "KARNATAKA" | `STATUS_VERIFIED_BENGALURU_CITY` | Verified Bids | **PASS** |
| Bengaluru Rural (Town) | City: "Nelamangala", District: "Bengaluru Rural" | `STATUS_OUTSIDE_TARGET` | Excluded | **PASS** |
| Dehradun, Uttarakhand | City: "Dehradun", District: "Dehradun" | `STATUS_OUTSIDE_TARGET` | Excluded | **PASS** |
| Jodhpur, Rajasthan | City: "Jodhpur", District: "Jodhpur" | `STATUS_OUTSIDE_TARGET` | Excluded | **PASS** |
| Buyer Bangalore + Delivery Jodhpur | Buyer: Bengaluru Urban, Delivery: Jodhpur | `STATUS_OUTSIDE_TARGET` | Excluded | **PASS** |
| Buyer Jodhpur + Delivery Bangalore Urban | Buyer: Jodhpur, Delivery: Bangalore Urban (560094) | `STATUS_VERIFIED_BENGALURU_URBAN` | Verified Bids | **PASS** |
| Ambiguous Bare Bangalore | "Bangalore" with "District Unknown" / no state context | `STATUS_PARTIALLY_VERIFIED` | Review Queue | **PASS** |
| Missing Delivery Location | All fields null / unextracted | `STATUS_UNKNOWN` | Review Queue | **PASS** |
