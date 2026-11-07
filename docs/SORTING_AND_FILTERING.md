# GeM BidWatch — Sorting & Filtering Specification

This document describes the server-side and client-side sorting algorithms, search mechanics, and combined filter logic implemented in `app.routers.bids` and `app.dashboard`.

---

## 1. Server-Side Sorting Options

All sorting modes are handled at the SQL query level in `GET /bids/`:

| `sort_by` Parameter | SQL Order Clause | Use Case |
| :--- | :--- | :--- |
| **`closing_soonest`** (Default)| `ORDER BY end_date ASC NULLS LAST` | Urgent opportunities needing immediate bid preparation. |
| **`latest_published`** | `ORDER BY start_date DESC NULLS LAST` | Most recently published tenders on GeM. |
| **`oldest_published`** | `ORDER BY start_date ASC NULLS LAST` | Longest-running active tenders. |
| **`closing_latest`** | `ORDER BY end_date DESC NULLS LAST` | Tenders with maximum time remaining. |
| **`newly_added`** | `ORDER BY first_seen_at DESC` | Most recently discovered bids by the scanner engine. |
| **`recently_updated`** | `ORDER BY updated_at DESC NULLS LAST` | Bids with recent corrigendum or status modifications. |
| **`highest_value`** | `ORDER BY estimated_value DESC NULLS LAST` | Highest value contracts. |
| **`lowest_value`** | `ORDER BY estimated_value ASC NULLS LAST` | Small and micro procurement opportunities. |

---

## 2. Multi-Filter Logic

Filters can be combined simultaneously without conflict:
- **`status`**: `active` (default), `closing_soon`, `expired`, `all`.
- **`state`**: Matches `consignee_state` or `buyer_state`.
- **`city`**: Matches `consignee_city` or `buyer_city`.
- **`keyword`**: Full-text search across `bid_number`, `category_name`, `dept_name`, and `ministry_name`.
- **`category`**: Substring filter against `category_name`.
- **`dept`**: Substring filter against `dept_name`.
- **`source_type`**: `LIVE_VERIFIED` vs `IMPORTED`.

---

## 3. Web Dashboard Interaction Design

- **Status Tabs:** Switch between Active Opportunities, Closing Soon, Expired Archive, and All Records with 1 click.
- **Sorting Select:** Instant server-side re-query preserving active filters.
- **Category Chips:** Quick client-side instant filtering across Printers, Toners, Refilling, and OEM Inks.
- **Unified Search:** Multi-token regex filtering across Tender ID, Department name, and City.
