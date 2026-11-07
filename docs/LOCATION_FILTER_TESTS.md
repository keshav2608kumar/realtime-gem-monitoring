# GeM BidWatch — Location Normalization & Dual Target Support (Bengaluru City & Urban District)

**Target Locations Supported:**
1. **Bengaluru City (Bangalore City)** (`STATUS_VERIFIED_BENGALURU_CITY`)
2. **Bengaluru Urban District** (`STATUS_VERIFIED_BENGALURU_URBAN`)

**Strict Rejection:**
- **Bengaluru Rural** (`STATUS_OUTSIDE_TARGET`)
- **Outside Districts & States** (Jodhpur, Dehradun, Patna, Delhi, etc. -> `STATUS_OUTSIDE_TARGET`)
- **Bare Ambiguous "Bangalore"** without state or district context -> `PARTIALLY_VERIFIED` (`REVIEW`, isolated from verified feed)

---

## 1. Complete 13-Test Scenario Verification Matrix

All 12 prompt scenarios and the alarm removal scenario are automated and verified via pytest in `backend/tests/test_location_and_alarm_removal.py`:

| Test # | Scenario Description | Input Location / Conditions | Target Status / Expected Behavior | Verification Status |
|:---:|:---|:---|:---|:---:|
| **1** | Bengaluru city | `city="Bengaluru", state="KARNATAKA"` | `STATUS_VERIFIED_BENGALURU_CITY` (ACCEPT) | **PASSED** |
| **2** | Bangalore city | `city="Bangalore", state="KARNATAKA"` or raw text `"Bangalore City, Karnataka"` | `STATUS_VERIFIED_BENGALURU_CITY` (ACCEPT) | **PASSED** |
| **3** | Bengaluru Urban district | `city="Bengaluru", district="Bengaluru Urban", state="KARNATAKA"` | `STATUS_VERIFIED_BENGALURU_URBAN` (ACCEPT) | **PASSED** |
| **4** | Bangalore Urban district | `city="Bangalore", district="Bangalore Urban", state="KARNATAKA"` | `STATUS_VERIFIED_BENGALURU_URBAN` (ACCEPT) | **PASSED** |
| **5** | Bengaluru Rural | `district="Bengaluru Rural"` or towns (Doddaballapur, Nelamangala, Devanahalli, Hoskote) | `STATUS_OUTSIDE_TARGET` (REJECT) | **PASSED** |
| **6** | Jodhpur | `city="Jodhpur", district="Jodhpur", state="RAJASTHAN"` | `STATUS_OUTSIDE_TARGET` (REJECT) | **PASSED** |
| **7** | Dehradun | `city="Dehradun", district="Dehradun", state="UTTARAKHAND"` | `STATUS_OUTSIDE_TARGET` (REJECT) | **PASSED** |
| **8** | Buyer Bangalore + delivery Jodhpur | Buyer: Bengaluru Urban; Delivery: Jodhpur, Rajasthan | `STATUS_OUTSIDE_TARGET` (REJECT) | **PASSED** |
| **9** | Buyer Jodhpur + delivery Bangalore Urban | Buyer: Jodhpur, Rajasthan; Delivery: Bangalore Urban (Vimanapura / HAL), Karnataka | `STATUS_VERIFIED_BENGALURU_URBAN` (ACCEPT) | **PASSED** |
| **10** | Ambiguous bare Bangalore | Bare `"Bangalore"` with no state/district or `"Bangalore, district unknown"` | `STATUS_PARTIALLY_VERIFIED` (REVIEW) | **PASSED** |
| **11** | Missing delivery location | All location fields `None` | `STATUS_UNKNOWN` (ISOLATED) | **PASSED** |
| **12** | 'All Bengaluru Targets' filter | Query `/bids/?location_target=all_bengaluru` | Returns both city-level and district-level records; excludes outside records | **PASSED** |
| **13** | Complete Alarm Feature Removal | HTML inspection & API alert acknowledgement | Zero audio oscillators, siren buttons, or autoplay permissions; visual alerts & ack work cleanly | **PASSED** |

---

## 2. Location Source Priority Rules

Delivery location is evaluated in strict order of authority:
1. **Priority 1: Verified PDF delivery/consignee address** (`pdf_delivery_*`) extracted from official bid PDF documents.
2. **Priority 2: Structured source delivery location** (`delivery_*`) provided directly by the GeM portal.
3. **Priority 3: Consignee administrative location** (`consignee_*`) provided in bid metadata.
- **Strict Exclusion:** The Buyer office location (`buyer_*`) is strictly excluded from determining delivery eligibility. Buyer HQ in Bangalore with delivery to Jodhpur is rejected; Buyer in New Delhi with delivery to Bengaluru Urban is accepted.

---

## 3. Usable Location Filter Options

The UI provides persistent, functional location filters:
- **`All Bengaluru Targets`** (`all_bengaluru`): Returns all bids verified for either Bengaluru City or Bengaluru Urban District.
- **`Bengaluru City`** (`bengaluru_city`): Filters specifically for city-level verified bids.
- **`Bengaluru Urban District`** (`bengaluru_urban`): Filters specifically for district-level verified bids.

Selection behavior:
- Persisted in browser `localStorage.getItem('gem_location_target')` across page reloads.
- Triggers live API requests (`/bids/?location_target=...`) and updates table and summary counters instantly.
- Displayed actively in the Active Filter summary bar chip alongside category selections.

---

## 4. Complete Removal of Alarm Feature

All alarm-related components have been purged:
- `btnAlarmToggle` removed from top navbar.
- Web Audio API oscillator, GainNode, audio context, and interval timers completely removed.
- Siren toggle state and audio autoplay permission requests removed.
- Visual Match Alert Banner (`activeAlertBanner`) and Modal (`redAlertModal`) preserved with "Dismiss & Acknowledge" button calling `POST /alerts/{id}/ack`.
