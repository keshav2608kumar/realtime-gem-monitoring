# GeM BidWatch — Location Normalization Specification

This document details the administrative mapping rules, alias dictionaries, confidence metrics, and isolation guarantees implemented in `app.services.location_normalizer`.

---

## 1. Objectives & Guarantees

1. **Isolation Guarantee:**
   - Jodhpur bids strictly resolve to `Jodhpur, RAJASTHAN`. Under no circumstances will a Jodhpur bid be classified under Dehradun or Bangalore.
   - Dehradun bids strictly resolve to `Dehradun, UTTARAKHAND`. Under no circumstances will a Dehradun bid be classified under Jodhpur or Bangalore.
   - Bengaluru / Bangalore bids resolve to `Bengaluru / Bangalore Urban, KARNATAKA`.
   - Unknown locations remain `UNKNOWN` with display text `"Not available from source"`.
2. **Confidence Ratings:**
   - **`VERIFIED`**: Exact match against official GeM administrative registry (state and city verified).
   - **`NORMALIZED`**: Resolved through recognized alias (e.g., `UTTARANCHAL` -> `UTTARAKHAND`, `ORISSA` -> `ODISHA`, or canonical city lookup).
   - **`AMBIGUOUS`**: Ambiguous token requiring manual review.
   - **`UNKNOWN`**: No geographic clues present in the record.

---

## 2. Administrative Mapping Structure

### Canonical State Registry (36 States & UTs)
- All 28 States and 8 Union Territories are supported with their standard abbreviation codes (AP, AR, AS, BR, CG, DL, GA, GJ, HR, HP, JH, JK, KA, KL, LA, LD, MP, MH, MN, ML, MZ, NL, OD, PB, PY, RJ, SK, TN, TS, TR, UP, UK, WB, etc.).

### Verified City to Administrative State Mappings
| City Key | Canonical City | Administrative District | State |
| :--- | :--- | :--- | :--- |
| `jodhpur` | Jodhpur | Jodhpur | **RAJASTHAN** |
| `jaipur` | Jaipur | Jaipur | **RAJASTHAN** |
| `kota` | Kota | Kota | **RAJASTHAN** |
| `dehradun` | Dehradun | Dehradun | **UTTARAKHAND** |
| `haridwar` | Haridwar | Haridwar | **UTTARAKHAND** |
| `roorkee` | Roorkee | Haridwar | **UTTARAKHAND** |
| `bangalore` | Bangalore | Bangalore Urban | **KARNATAKA** |
| `bengaluru` | Bengaluru | Bangalore Urban | **KARNATAKA** |
| `bangalore urban`| Bangalore Urban| Bangalore Urban | **KARNATAKA** |
| `mysore` / `mysuru`| Mysuru | Mysuru | **KARNATAKA** |
| `patna` | Patna | Patna | **BIHAR** |
| `munger` | Munger | Munger | **BIHAR** |
| `delhi` | Delhi | New Delhi | **DELHI** |
| `mumbai` | Mumbai | Mumbai | **MAHARASHTRA** |
| `pune` | Pune | Pune | **MAHARASHTRA** |
| `lucknow` | Lucknow | Lucknow | **UTTAR PRADESH** |
| `kolkata` | Kolkata | Kolkata | **WEST BENGAL** |
| `chennai` | Chennai | Chennai | **TAMIL NADU** |
| `hyderabad` | Hyderabad | Hyderabad | **TELANGANA** |

---

## 3. Resolution Logic Flow

```
Input: raw_text (Department / Buyer name), city_hint, state_hint
                       │
                       ▼
              Clean & Collapse Whitespace
                       │
                       ▼
             Match City in Registry?
            ├── YES ──> Assign Canonical City, District, and State (VERIFIED/NORMALIZED)
            └── NO  ──>
                       │
                       ▼
             Match State in Registry?
            ├── YES ──> Assign Canonical State (NORMALIZED)
            └── NO  ──>
                       │
                       ▼
       Scan raw_text for known city word boundaries
            ├── MATCH ──> Assign Extracted Location (NORMALIZED)
            └── NONE  ──> Return UNKNOWN ("Not available from source")
```

---

## 4. Verification Test Cases

The test suite in `tests/test_audit_and_upgrades.py` validates that:
- `normalize_location(city_hint="Jodhpur", state_hint="RAJASTHAN")` -> `Jodhpur, RAJASTHAN`
- `normalize_location(city_hint="Dehradun", state_hint="UTTARAKHAND")` -> `Dehradun, UTTARAKHAND`
- `normalize_location(city_hint="RandomCity", state_hint="")` -> `Not available from source` (Confidence: `UNKNOWN`)
- `normalize_location(city_hint="", state_hint="")` -> `Not available from source` (Confidence: `UNKNOWN`)
