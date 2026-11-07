# Location Verification & Segregation Rules — GeM BidWatch

## Overview
This document defines the strict administrative location verification rules, postal PIN code validation mappings, location tier segregation, and query resolution paths implemented in **GeM BidWatch**.

---

## 1. Location Verification Lifecycle Statuses

Every location extracted from bid metadata or official PDF documents is classified into one of five definitive statuses:

| Status | Confidence Score | Definition & Criteria |
|---|---|---|
| **`VERIFIED`** | **0.85 – 0.95** | Complete address with validated State, City/District, and a 6-digit PIN code matching the state's postal circle prefix. |
| **`PARTIALLY_VERIFIED`** | **0.60 – 0.75** | State and City/District identified and validated, but PIN code is missing or unverified. |
| **`AMBIGUOUS`** | **0.30 – 0.45** | Contradictory locations mentioned across pages without clear consignment mapping (e.g. buyer in Delhi, annexure mentioning multiple depot addresses). |
| **`UNKNOWN`** | **0.00 – 0.15** | Text was extracted from the document or metadata, but no recognizable Indian administrative location was found. |
| **`PDF_UNAVAILABLE`** | **0.00** | Document attachment is missing, URL returned 404, or request was blocked by anti-bot/firewall. |

---

## 2. Segregated Location Layers

To prevent geographic contamination (e.g., Delhi buyer headquarters falsely overwriting a Jodhpur or Bangalore delivery depot), the system maintains distinct, segregated database columns:

```
┌─────────────────────────────────────────────────────────────┐
│                       GeM Tender Record                     │
├──────────────────────────────┬──────────────────────────────┤
│ Buyer Location Layer:        │ Consignee Location Layer:    │
│ - buyer_state                │ - consignee_state            │
│ - buyer_district             │ - consignee_district         │
│ - buyer_city                 │ - consignee_city             │
├──────────────────────────────┼──────────────────────────────┤
│ Delivery Location Layer:     │ PDF Extracted Document Layer:│
│ - delivery_state             │ - pdf_delivery_state         │
│ - delivery_district          │ - pdf_delivery_district      │
│ - delivery_city              │ - pdf_delivery_city          │
│ - delivery_address           │ - pdf_delivery_pincode       │
│                              │ - pdf_delivery_consignee     │
│                              │ - pdf_delivery_org           │
│                              │ - pdf_delivery_address (raw) │
│                              │ - pdf_page_number            │
│                              │ - pdf_verification_status   │
└──────────────────────────────┴──────────────────────────────┘
```

---

## 3. Postal Index Number (PIN Code) Verification Matrix

Indian postal PIN codes consist of 6 digits (`[1-9][0-9]{5}`). The first 2 digits designate the Postal Circle / State. The extraction engine verifies the extracted PIN code prefix against the identified state:

| PIN Prefix (First 2 Digits) | Associated Indian Postal Circle / State |
|---|---|
| `11` | Delhi |
| `12`, `13` | Haryana |
| `14`, `15`, `16` | Punjab, Chandigarh |
| `17` | Himachal Pradesh |
| `18`, `19` | Jammu & Kashmir, Ladakh |
| `20`, `21`, `22`, `23`, `24`, `25`, `26`, `27`, `28` | Uttar Pradesh, Uttarakhand |
| `30`, `31`, `32`, `33`, `34` | Rajasthan (e.g. `342xxx` = Jodhpur, `302xxx` = Jaipur) |
| `36`, `37`, `38`, `39` | Gujarat, Daman & Diu, Dadra & Nagar Haveli |
| `40`, `41`, `42`, `43`, `44` | Maharashtra, Goa (e.g. `400xxx` = Mumbai, `411xxx` = Pune) |
| `45`, `46`, `47`, `48` | Madhya Pradesh |
| `49` | Chhattisgarh |
| `50` | Telangana (e.g. `500xxx` = Hyderabad) |
| `51`, `52`, `53` | Andhra Pradesh |
| `56`, `57`, `58`, `59` | Karnataka (e.g. `560xxx` = Bangalore, `570xxx` = Mysore) |
| `60`, `61`, `62`, `63`, `64` | Tamil Nadu, Puducherry (e.g. `600xxx` = Chennai) |
| `67`, `68`, `69` | Kerala, Lakshadweep |
| `70`, `71`, `72`, `73`, `74` | West Bengal, Andaman & Nicobar (e.g. `700xxx` = Kolkata) |
| `75`, `76`, `77` | Odisha |
| `78`, `79` | Assam, Meghalaya, Mizoram, Manipur, Tripura, Nagaland, Arunachal Pradesh |
| `80`, `81`, `82`, `83`, `84`, `85` | Bihar, Jharkhand (e.g. `800xxx` = Patna, `811xxx` = Munger) |

### Confidence Rule:
When both the textual state name and the 6-digit PIN code match the postal circle table above, the extraction achieves maximum confidence (`0.95` — `VERIFIED`).

---

## 4. Location Filter Query Resolution (`location_type`)

The `/bids/` endpoint supports targeted location queries using the `location_type` parameter:

| `location_type` Value | Filter Target | Use Case |
|---|---|---|
| `consignee` (Default) | `consignee_state`, `consignee_city`, `buyer_state`, `buyer_city` | Standard procurement monitoring. |
| `pdf_delivery` | `pdf_delivery_state`, `pdf_delivery_city` | Strict matching against physical consignment delivery location extracted from bid PDF. |
| `buyer` | `buyer_state`, `buyer_city` | Matches procuring department headquarters. |
| `delivery` | `delivery_state`, `delivery_city` | Matches explicit tender delivery address field. |
| `any` | All available location layers combined via `OR` | Comprehensive broad search across all location fields. |

---

## 5. False Default Prevention Guardrails

1. **Zero Bangalore Fallback**: Missing locations are recorded as `None` and display `"Not available from source"`. Under no circumstances is Bangalore or any default city substituted.
2. **Jodhpur vs Dehradun Isolation**: Administrative lookups strictly isolate Rajasthan cities (Jodhpur, Jaipur, Kota) from Uttarakhand cities (Dehradun, Haridwar, Rishikesh).
3. **Word Boundary Enforcing**: Searches match complete word boundaries (`\bbangalore\b` matches "Bangalore Urban", but will never match "Mangalore").
