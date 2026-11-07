# GeM BidWatch — Product Category Test Report

**Document Date:** 2026-11-07  
**Module:** `app.services.category_service`, `app.routers.bids`  
**Target:** 7 Exact Official GeM Product Categories

---

## 1. Official Category Definitions & Canonical Identifiers

All seven required categories are preserved verbatim with immutable canonical identifiers:

| Category ID | Verbatim Official Display Name | Short Code | Domain Scope |
|---|---|---|---|
| `TONER_INK_PRINTER_CONSUMABLES` | Toner Cartridges / Ink Cartridges / Consumables for Printers | `TONER_CART` | Laser toner, inkjet cartridges, drum units |
| `SCANNER_V3` | Scanner (V3) | `SCANNER_V3` | GeM Version 3 document and flatbed scanners |
| `A4_LEGAL_SIZE_MFP` | A4 and Legal Size Multifunction Printer (MFP) | `A4_MFP` | Multi-function printer/scanner (A4/Legal) |
| `A3_SIZE_MFP` | A3 Size Multifunction Printer (MFP) | `A3_MFP` | Commercial heavy-duty A3 digital copiers |
| `COMPUTER_PRINTER_V2` | Computer Printer (V2) | `PRINTER_V2` | GeM Version 2 standard office printers |
| `HIGH_END_DESKTOP` | High End Desktop Computer | `HIGH_END_PC` | Enterprise workstations and high-spec PCs |
| `HIGH_END_LAPTOP_NOTEBOOK`| High End Laptop - Notebook | `HIGH_END_LAPTOP` | Executive notebooks, mobile workstations |

---

## 2. API & Backend Filtering Capabilities

1. **Independent Category Filtering:**
   - Query: `GET /bids/?categories=TONER_INK_PRINTER_CONSUMABLES`
   - Returns bids matching this specific category.
2. **Multiple Category Selection (Union Filtering):**
   - Query: `GET /bids/?categories=SCANNER_V3&categories=COMPUTER_PRINTER_V2`
   - Generates SQL: `WHERE Bid.category_key IN ('SCANNER_V3', 'COMPUTER_PRINTER_V2') OR Bid.category_name LIKE '%Scanner (V3)%' OR Bid.category_name LIKE '%Computer Printer (V2)%'`
   - Returns only bids belonging to one of the selected categories.
3. **Select All & Clear All:**
   - UI provides "Select All" (submits all 7 categories) and "Clear All" (clears category restrictions).
4. **Persistence:**
   - Category selections are stored in `localStorage` under `gem_bidwatch_selected_categories` and restored upon reload.

---

## 3. Test Matrix & Verification Evidence

| Test Scenario | Test Input / Query | Expected Output | Status |
|---|---|---|---|
| Exact Match 1 | `Toner Cartridges / Ink Cartridges / Consumables for Printers` | Key: `TONER_INK_PRINTER_CONSUMABLES`, Status: `VERIFIED` | **PASS** |
| Exact Match 2 | `Scanner (V3)` | Key: `SCANNER_V3`, Status: `VERIFIED` | **PASS** |
| Exact Match 3 | `A4 and Legal Size Multifunction Printer (MFP)` | Key: `A4_LEGAL_SIZE_MFP`, Status: `VERIFIED` | **PASS** |
| Exact Match 4 | `A3 Size Multifunction Printer (MFP)` | Key: `A3_SIZE_MFP`, Status: `VERIFIED` | **PASS** |
| Exact Match 5 | `Computer Printer (V2)` | Key: `COMPUTER_PRINTER_V2`, Status: `VERIFIED` | **PASS** |
| Exact Match 6 | `High End Desktop Computer` | Key: `HIGH_END_DESKTOP`, Status: `VERIFIED` | **PASS** |
| Exact Match 7 | `High End Laptop - Notebook` | Key: `HIGH_END_LAPTOP_NOTEBOOK`, Status: `VERIFIED` | **PASS** |
| Variant Mapping | `Toner Cartridges / Ink Cartridges / Consumables for Printers (HP, Canon OEM)` | Key: `TONER_INK_PRINTER_CONSUMABLES`, Status: `MAPPED` | **PASS** |
| Version Protection | `Computer Printer (V2)` vs `Computer Printer (V1)` | V2 matches `COMPUTER_PRINTER_V2`; V1 is distinct/unmapped | **PASS** |
| Size Segregation | `A4 and Legal Size MFP` vs `A3 Size MFP` | Distinct keys assigned; no cross-contamination | **PASS** |
| Unrelated Category | `Office Wooden Furniture Tables` | Key: `None`, Status: `UNMAPPED` | **PASS** |
| Missing Category | `None` / empty | Key: `None`, Status: `UNKNOWN` | **PASS** |
| Multi-Category Query | Query with `SCANNER_V3` + `COMPUTER_PRINTER_V2` | 2 records returned; exactly matching keys | **PASS** |
