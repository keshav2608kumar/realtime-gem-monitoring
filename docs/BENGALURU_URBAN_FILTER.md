# Strict Bengaluru Urban Target Location Filter Specification
## GeM BidWatch Enterprise Procurement Radar

---

## 1. Executive Mandate
GeM BidWatch is strictly configured to monitor **ONLY** tenders whose verified delivery/consignee destination is located within **Bengaluru Urban, Karnataka**. 

Bids destined for other districts, rural taluks, or outside states are strictly prevented from appearing in the verified matching feed and are barred from triggering auditory or notification alerts.

---

## 2. Fixed Target Location Definition

| Attribute | Canonical Value |
|---|---|
| **Country** | India |
| **State** | Karnataka (`KARNATAKA`) |
| **District** | Bengaluru Urban |
| **City** | Bengaluru (Bangalore) |
| **Target Display** | `Bengaluru Urban, Karnataka` |
| **PIN Code Range** | `560001` through `560110` |

---

## 3. Verified Aliases Normalization
The system recognizes the following verified aliases and normalizes them to `Bengaluru Urban, Karnataka` while preserving the full original address for legal auditability:
- `Bengaluru`
- `Bangalore`
- `Bangalore Urban`
- `Bengaluru Urban`
- `Bengaluru, Karnataka`
- `Bangalore, Karnataka`

---

## 4. Bengaluru Urban vs. Bengaluru Rural Strict Separation

A major vulnerability in naive scrapers is confusing **Bengaluru Urban** with **Bengaluru Rural**. 

In GeM BidWatch:
1. **Explicit Rural Mentions:** Any address containing `"Bengaluru Rural"`, `"Bangalore Rural"`, or district flagged as `Rural` is classified as `OUTSIDE_TARGET` and **REJECTED**.
2. **Peripheral Taluks & Towns:** Known rural taluks are explicitly recognized and classified as `OUTSIDE_TARGET`:
   - `Doddaballapur` / `Doddaballapura`
   - `Nelamangala`
   - `Devanahalli`
   - `Hoskote` / `Hosakote`
   - `Kanakapura`
   - `Ramanagara` / `Channapatna` / `Magadi`
3. **Postal PIN Zones:**
   - `560001` to `560110`: **Bengaluru Urban** (`VERIFIED_BENGALURU_URBAN`)
   - `561000` to `562999` (e.g., 562110 Devanahalli, 562114 Hoskote): **Bengaluru Rural** (`OUTSIDE_TARGET`)

---

## 5. Standardized Location Verification Statuses

| Status | Definition | Feed Placement | Alerts Triggered? |
|---|---|---|---|
| `VERIFIED_BENGALURU_URBAN` | Explicitly verified delivery address within Bengaluru Urban (PIN, district, or verified campus). | Default Matching Feed (`scope=bengaluru_urban`) | **YES** (if category matches) |
| `PARTIALLY_VERIFIED` | Mentions Bangalore/Bengaluru but district is unknown or context is incomplete. | Isolated Review Queue (`scope=review`) | **NO** |
| `AMBIGUOUS` | Conflicting location signals detected (e.g. buyer in Jodhpur, partial mention of Bangalore without confirmation). | Isolated Review Queue (`scope=review`) | **NO** |
| `OUTSIDE_TARGET` | Delivery verified in another district (e.g., Bengaluru Rural, Mysore, Dehradun, Jodhpur, Patna). | Outside Archive (`scope=outside`) | **NO** |
| `UNKNOWN` | Delivery location absent or unextractable from source record or PDF. | Review Queue / Unknown | **NO** |

---

## 6. Priority Delivery Location Resolution
Buyer organization address (headquarters) often does not match the actual delivery location.

### Resolution Priority Hierarchy:
1. **Priority 1: Verified PDF Extracted Delivery Address** (`pdf_delivery_*`):
   - Parsed from the official bid PDF document's consignee table on final pages.
2. **Priority 2: Structured Source Delivery Location** (`delivery_*`):
   - Parsed from structured delivery fields in the GeM tender payload.
3. **Priority 3: Consignee Location** (`consignee_*`):
   - Consignee reporting officer station and address.
4. **Buyer Location Office (`buyer_*`) is EXCLUDED from Delivery Matching:**
   - Buyer in Bengaluru, Delivery in Jodhpur ➔ **REJECT** (`OUTSIDE_TARGET`)
   - Buyer in Jodhpur/Delhi, Delivery in Bengaluru Urban ➔ **MATCH** (`VERIFIED_BENGALURU_URBAN`)

---

## 7. Backend Query & Filter Enforcement

In `app/gem/filter_matcher.py`:
```python
eff_status, eff_conf, eff_city, eff_dist, eff_state = resolve_effective_bid_delivery_location(bid)

if profile_targets_bengaluru:
    if eff_status != STATUS_VERIFIED_BENGALURU_URBAN:
        return MatchResult(False, [], f"Location rejected: Effective delivery status is '{eff_status}'")
```

In `app/routers/bids.py`:
- `GET /bids/?scope=bengaluru_urban`: Strictly filters `Bid.target_location_status == 'VERIFIED_BENGALURU_URBAN'`.
- `GET /bids/?scope=review`: Strictly filters `Bid.target_location_status.in_(['PARTIALLY_VERIFIED', 'AMBIGUOUS', 'UNKNOWN'])`.
- `GET /bids/?scope=outside`: Strictly filters `Bid.target_location_status == 'OUTSIDE_TARGET'`.

---

## 8. Verification Results Matrix

| Input Condition | Target Status | Feed Destination | Result |
|---|---|---|---|
| `Bengaluru Urban, Karnataka` | `VERIFIED_BENGALURU_URBAN` | Matching Feed | **MATCH** |
| `Bangalore Urban, Karnataka` | `VERIFIED_BENGALURU_URBAN` | Matching Feed | **MATCH** |
| `Bengaluru, verified Bengaluru Urban district` | `VERIFIED_BENGALURU_URBAN` | Matching Feed | **MATCH** |
| `Jodhpur, Rajasthan` | `OUTSIDE_TARGET` | Outside Archive | **REJECT** |
| `Dehradun, Uttarakhand` | `OUTSIDE_TARGET` | Outside Archive | **REJECT** |
| `Patna, Bihar` | `OUTSIDE_TARGET` | Outside Archive | **REJECT** |
| `Bengaluru Rural, Karnataka` | `OUTSIDE_TARGET` | Outside Archive | **REJECT** |
| `Bangalore, district unknown` | `PARTIALLY_VERIFIED` | Review Queue | **REVIEW** |
| Missing / None | `UNKNOWN` | Review Queue | **UNKNOWN** |
| Buyer: Bengaluru, Delivery: Jodhpur | `OUTSIDE_TARGET` | Outside Archive | **REJECT** |
| Buyer: Jodhpur, Delivery: Bengaluru Urban | `VERIFIED_BENGALURU_URBAN` | Matching Feed | **MATCH** |
