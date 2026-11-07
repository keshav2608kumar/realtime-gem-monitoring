# GeM BidWatch — Date & Time Handling Specification

This document details the datetime parsing architecture, storage conventions, and timezone conversion rules implemented in `app.services.datetime_service`.

---

## 1. Core Principles

1. **Storage in UTC:**
   All timestamps stored in the SQLite / PostgreSQL database are strictly stored as timezone-aware UTC datetime instances (`DateTime(timezone=True)`).
2. **Display in Indian Standard Time (IST):**
   User-facing interfaces (Web Dashboard, API responses, Android application) display dates and times in `Asia/Kolkata` (UTC+05:30).
3. **Never Invent Timestamps:**
   - If a source payload lacks a publication date, it remains `None` and displays `"Not available from source"`.
   - The current clock time or ingestion timestamp is **never** substituted for publication date.
   - If a source payload provides date only without time, midnight is not assumed to be midday; the time string displays `"Time not specified"`.

---

## 2. Supported Ingestion Date Formats

The parser `parse_datetime()` handles:
- ISO 8601 with trailing Z: `2026-11-16T15:00:00Z`
- ISO 8601 with explicit offset: `2026-11-16T15:00:00+05:30`
- Standard Indian procurement format: `16-11-2026 15:00:00`
- Space-separated format: `2026-11-16 15:00:00`
- Slash-separated format: `16/11/2026 15:00:00`
- Date-only strings: `2026-11-16` or `16-11-2026`

---

## 3. Formatting Standards

| Field | Example Display String | Format Pattern |
| :--- | :--- | :--- |
| `published_date` | `07 Nov 2026` | `%d %b %Y` (IST) |
| `published_time` | `03:30 PM` | `%I:%M %p` (IST) |
| `end_date_formatted` | `16 Nov 2026` | `%d %b %Y` (IST) |
| `end_time_formatted` | `05:00 PM` | `%I:%M %p` (IST) |
| `time_remaining` | `8d 2h remaining` | Dynamic Countdown |
| `time_remaining` (Closing soon) | `Closing in 3h 15m` | Dynamic Countdown |
| `time_remaining` (Expired) | `Expired 2d ago` | Historical Elapsed |

---

## 4. Time Remaining Calculation Logic

`compute_time_remaining(end_dt: datetime, now_utc: datetime)` computes:
- If `end_dt <= now_utc`:
  - `is_expired = True`
  - `hours_left = 0.0`
  - `human = "Expired {days}d ago"` or `"Expired {hours}h ago"`
- If `end_dt > now_utc`:
  - `is_expired = False`
  - If days > 0: `human = "{days}d {hours}h remaining"`
  - If days == 0 and hours > 0: `human = "Closing in {hours}h {mins}m"`
  - If days == 0 and hours == 0: `human = "Closing in {mins}m"`
