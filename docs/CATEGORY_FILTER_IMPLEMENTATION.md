# Product Category Filter Implementation — GeM BidWatch

## Overview
This document details the architectural design, database schemas, matching logic, and frontend implementation of the seven canonical Government e-Marketplace (GeM) product categories in **GeM BidWatch**.

---

## 1. The Seven Exact GeM Product Categories

All categories are preserved with their exact official names, stable identifiers, and dedicated short codes:

| # | Official GeM Display Name | Stable Identifier | Short Code | Scope & Description |
|---|---|---|---|---|
| 1 | **Toner Cartridges / Ink Cartridges / Consumables for Printers** | `TONER_INK_PRINTER_CONSUMABLES` | `TONER_CART` | Laser toner, inkjet cartridges, photoconductor drums, ribbons, and printer consumables. |
| 2 | **Scanner (V3)** | `SCANNER_V3` | `SCANNER_V3` | GeM Version 3 document and flatbed digital scanning equipment. |
| 3 | **A4 and Legal Size Multifunction Printer (MFP)** | `A4_LEGAL_SIZE_MFP` | `A4_MFP` | A4 and Legal format multi-function printing, scanning, and copying devices. |
| 4 | **A3 Size Multifunction Printer (MFP)** | `A3_SIZE_MFP` | `A3_MFP` | Heavy-duty A3 format commercial digital multifunction printers and network copiers. |
| 5 | **Computer Printer (V2)** | `COMPUTER_PRINTER_V2` | `PRINTER_V2` | GeM Version 2 standard departmental and workgroup laser/inkjet printers. |
| 6 | **High End Desktop Computer** | `HIGH_END_DESKTOP` | `HIGH_END_PC` | Enterprise workstations, CAD/CAM systems, and high-performance desktop computers. |
| 7 | **High End Laptop - Notebook** | `HIGH_END_LAPTOP_NOTEBOOK` | `HIGH_END_LAPTOP` | High-performance mobile workstations, ultrabooks, and executive notebooks. |

---

## 2. Category Normalization & Matching Rules (`category_service.py`)

Matching is performed strictly without loose substring queries that produce false positives.

### Mapping Lifecycle Statuses:
- **`VERIFIED`**: Exact string equality against the official canonical name or known authoritative GeM alias.
- **`MAPPED`**: Controlled regex match against authoritative category text while respecting explicit version numbers (e.g., V2 vs V3).
- **`UNMAPPED`**: Category string exists from GeM source but does not belong to any of the seven target categories (e.g., Office Furniture, Medical Equipment).
- **`UNKNOWN`**: Category text is null, empty, or completely ambiguous.

### Strict Version Separation & Guardrails:
- **`Computer Printer (V2)`**: Requires explicit `V2` qualification. A legacy bid mentioning `Computer Printer (V1)` is classified as `UNMAPPED` and will never match `COMPUTER_PRINTER_V2`.
- **`Scanner (V3)`**: Requires explicit `V3` qualification. Medical scanners (e.g. Ultrasound Scanner) or generic scanners are classified as `UNMAPPED`.
- **`A4 vs A3 MFP`**: A4 and A3 size MFPs are segregated into distinct categories using boundary-enforced regex patterns (`\ba4\b` vs `\ba3\b`).

---

## 3. Database Schema Extensions

### `bids` Table:
- `category_key` (`VARCHAR(100)`, indexed): Stores the stable canonical identifier (e.g. `COMPUTER_PRINTER_V2`).
- `category_mapping_status` (`VARCHAR(50)`): `VERIFIED`, `MAPPED`, `UNMAPPED`, `UNKNOWN`.

### `profiles` Table:
- `categories` (`JSON` / `TEXT`): Stores an array of selected category keys for a monitoring profile (e.g., `["TONER_INK_PRINTER_CONSUMABLES", "COMPUTER_PRINTER_V2"]`).

### Automatic Data Migration & Backfill (`database.py`):
During `init_db()` and `migrate_db()`, missing columns are safely added to SQLite/PostgreSQL without data loss. An automatic backfill process scans all existing bids and derives their `category_key` and `category_mapping_status` using `category_service.match_category()`.

---

## 4. Backend Query & Filter Engine Integration (`routers/bids.py`)

The `/bids/` API endpoint supports multi-select category filtering:
```http
GET /bids/?categories=SCANNER_V3&categories=COMPUTER_PRINTER_V2&status=active
```
Comma-separated lists are also supported:
```http
GET /bids/?categories=SCANNER_V3,COMPUTER_PRINTER_V2
```

### Multi-Category Filter Logic:
1. Category keys are parsed, cleaned, and validated against `CATEGORIES_BY_ID`.
2. Bids matching **any** of the selected categories (`OR` logic among categories) are included.
3. Category filters combine seamlessly with existing location (`state`, `city`), lifecycle (`status`), search query (`keyword`), and department (`dept`) filters using standard boolean `AND` conjunctions.

---

## 5. Profile Matching Engine (`gem/filter_matcher.py`)

When an Indian scanner node or background task pushes new tenders via `/bids/batch-sync`:
1. If `profile.categories` is configured, the matcher checks if `bid.category_key` is in the allowed list.
2. If `bid.category_key` is not yet populated, it is dynamically computed using `category_service.match_category()`.
3. If the bid category does not match, the tender is rejected immediately:
   ```python
   return MatchResult(False, [], f"Category mismatch: Bid category '{bid_cat_key}' not in profile categories")
   ```
4. If it matches, the matched category ID is recorded in the alert's `match_reason`.

---

## 6. Frontend User Interface Implementation (`dashboard.py`)

A dedicated **Official GeM Product Category Filter Panel** is placed prominently on the web dashboard:

1. **Seven Multi-Select Checkboxes**:
   - Each category displays its exact official name.
   - Interactive checkbox state indicates active inclusion.
2. **Bulk Actions**:
   - **Select All**: Enables all seven categories with a single click.
   - **Clear All**: Clears all categories.
3. **Selection Counter Badge**:
   - Dynamically displays `N of 7 Selected`.
4. **Active Filter Summary**:
   - Renders individual dismissible category chips showing active filters.
5. **Persistence Across Reloads**:
   - State is automatically saved to `localStorage.getItem('gem_selected_categories')`.
   - Selections persist across browser refreshes and sessions.
6. **Responsive Layout**:
   - Uses Tailwind CSS grid (`grid-cols-1 md:grid-cols-2 lg:grid-cols-4`) for mobile, tablet, and desktop form factors.
