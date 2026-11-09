# GeM BidWatch — Seven Product Category Filters Report
**Module:** `backend/app/services/category_service.py`  
**Date:** 09 November 2026  

---

## 1. Canonical Categories Registry

The application enforces filtering against 7 official GeM procurement categories:

| ID | Canonical Key | Official GeM Category Name | Associated Aliases |
|---|---|---|---|
| **1** | `TONER_INK_PRINTER_CONSUMABLES` | Toner Cartridges / Ink Cartridges / Consumables for Printers | OEM Toner, Ink Cartridge, Printer Consumables, Ribbon |
| **2** | `SCANNER_V3` | Scanner (V3) | Document Scanner, Flatbed Scanner, Book Scanner |
| **3** | `A4_LEGAL_SIZE_MFP` | A4 and Legal Size Multifunction Printer (MFP) | A4 MFP, Network MFP, Heavy Duty Office MFP |
| **4** | `A3_SIZE_MFP` | A3 Size Multifunction Printer (MFP) | A3 Digital Copier, A3 Multifunction |
| **5** | `COMPUTER_PRINTER_V2` | Computer Printer (V2) | Single Function Printer, Laser Printer V2, Inkjet V2 |
| **6** | `HIGH_END_DESKTOP` | High End Desktop Computer | Workstation Computer, CAD Desktop, Engineering PC |
| **7** | `HIGH_END_LAPTOP_NOTEBOOK` | High End Laptop - Notebook | Heavy Duty Laptop, Mobile Workstation, Ultrabook |

---

## 2. Server-Side Execution

Category filtering is executed server-side via SQL query predicates in `backend/app/routers/bids.py`:
- `categories`: Array of canonical category keys passed via query parameters (e.g. `?categories=TONER_INK_PRINTER_CONSUMABLES,COMPUTER_PRINTER_V2`).
- Backend queries filter using `Bid.category_key.in_(selected_keys)` combined with indexed substring match on `Bid.category_name`.
- When all 7 categories are selected, the feed displays all matching items; when specific checkboxes are cleared, the feed filters reactively without page reload.
