# GeM BidWatch — Location Normalization & Strict Bengaluru Urban Scoping

**Target District:** `Bengaluru Urban, Karnataka, India` (Mandatory Target)  
**Strict Boundary:** Only bids whose verified consignee delivery location is within Bengaluru Urban enter the verified feed. All other districts, states, and ambiguous records are strictly isolated.

---

## 1. Geographical Normalization Matrix

The system implements strict deterministic classification in `location_normalizer.py`:

| Input Location Details | Expected Target Status | Classification Rule |
|:---|:---:|:---|
| Bangalore Urban, Karnataka | `VERIFIED_BENGALURU_URBAN` | Explicit district & state match |
| Bengaluru, Karnataka (PIN 560094) | `VERIFIED_BENGALURU_URBAN` | Bengaluru Urban PIN range (`560001` - `560110`) |
| ISRO Satellite Centre (URSC), Bangalore | `VERIFIED_BENGALURU_URBAN` | Known Urban institutional campus |
| Governors Office (Raj Bhavan), Bangalore | `VERIFIED_BENGALURU_URBAN` | Known Urban institutional campus |
| DRDO - ADE, Bangalore | `VERIFIED_BENGALURU_URBAN` | Known Urban institutional campus |
| Doddaballapur, Karnataka | `OUTSIDE_TARGET` | Bengaluru Rural taluk strictly rejected |
| Nelamangala, Karnataka | `OUTSIDE_TARGET` | Bengaluru Rural taluk strictly rejected |
| Devanahalli, Karnataka | `OUTSIDE_TARGET` | Bengaluru Rural taluk strictly rejected |
| Hoskote, Karnataka | `OUTSIDE_TARGET` | Bengaluru Rural taluk strictly rejected |
| Kanakapura / Ramanagara | `OUTSIDE_TARGET` | Ramanagara district strictly rejected |
| PIN 562123 (Bengaluru Rural) | `OUTSIDE_TARGET` | PIN range (`561000` - `562999`) rejected |
| Jodhpur, Rajasthan | `OUTSIDE_TARGET` | Outside state; never defaults to Bangalore |
| Dehradun, Uttarakhand | `OUTSIDE_TARGET` | Outside state; never defaults to Bangalore |
| Patna, Bihar | `OUTSIDE_TARGET` | Outside state; never defaults to Bangalore |
| New Delhi, Delhi | `OUTSIDE_TARGET` | Outside state; never defaults to Bangalore |
| Bangalore (Bare name, no state, no PIN) | `PARTIALLY_VERIFIED` | Requires manual review; isolated from feed |
| Ambiguous / Conflicting locations | `AMBIGUOUS` | Placed in review feed |

---

## 2. Segregation of Delivery vs Buyer Office

A critical procurement requirement is that **the buyer's corporate office location must never dictate delivery eligibility**:

* **Scenario:** A Central Ministry based in New Delhi issues a tender with delivery to an ISRO facility in Bengaluru Urban.
  - Buyer Location: New Delhi
  - Delivery Location: Bengaluru Urban
  - **Verdict:** MATCH (`VERIFIED_BENGALURU_URBAN`)
* **Scenario:** An organization head-quartered in Bengaluru issues a tender for a field office in Dehradun or Jodhpur.
  - Buyer Location: Bengaluru
  - Delivery Location: Jodhpur
  - **Verdict:** OUTSIDE TARGET (`OUTSIDE_TARGET`)

### Precedence Hierarchy:
1. **Priority 1:** Verified PDF delivery address extracted from document tables (`pdf_delivery_*`).
2. **Priority 2:** Structured GeM source delivery location (`delivery_*`).
3. **Priority 3:** Consignee administrative location (`consignee_*`).
4. **Excluded:** Buyer office address (`buyer_*`) is never used to determine target matching.

---

## 3. Regression Test Verification

Automated test cases in `backend/tests/test_bengaluru_urban_matching.py` and `backend/tests/test_audit_and_upgrades.py`:

```bash
pytest backend/tests/test_bengaluru_urban_matching.py
```

* `test_bengaluru_urban_classification_matrix`: **PASSED**
* `test_rural_towns_strictly_rejected`: **PASSED**
* `test_pincode_boundary_validation`: **PASSED**
* `test_buyer_office_never_determines_delivery`: **PASSED**
* `test_profile_matcher_strict_bengaluru_urban`: **PASSED**
* `test_api_scope_and_stats`: **PASSED**
