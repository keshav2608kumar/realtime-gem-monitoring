"""
GeM BidWatch — Datetime & Timezone Service
Handles robust parsing, UTC storage, and Asia/Kolkata (IST) display conversion.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any
from zoneinfo import ZoneInfo

# Official Indian Standard Time (IST)
IST_TZ = ZoneInfo("Asia/Kolkata")
UTC_TZ = timezone.utc


def parse_datetime(dt_input: Any) -> Optional[datetime]:
    """
    Parse a datetime from various representations into a timezone-aware UTC datetime.
    Supports:
    - datetime instances (naive assumed UTC, or converted from timezone)
    - ISO strings (with Z or offsets)
    - Standard GeM formats (YYYY-MM-DD HH:MM:SS, DD-MM-YYYY HH:MM:SS)
    - Date-only formats (YYYY-MM-DD)
    """
    if dt_input is None:
        return None

    if isinstance(dt_input, datetime):
        if dt_input.tzinfo is None:
            return dt_input.replace(tzinfo=UTC_TZ)
        return dt_input.astimezone(UTC_TZ)

    s = str(dt_input).strip()
    if not s or s.lower() in ("none", "null", ""):
        return None

    # Handle ISO formats
    try:
        iso_clean = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso_clean)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC_TZ)
        return dt.astimezone(UTC_TZ)
    except (ValueError, TypeError):
        pass

    # Try common explicit patterns
    patterns = [
        "%Y-%m-%d %H:%M:%S",
        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%d-%m-%Y %I:%M %p",
        "%d/%m/%Y %I:%M %p",
        "%Y-%m-%d %I:%M %p",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
    ]

    for p in patterns:
        try:
            dt = datetime.strptime(s, p)
            # Default naive parsed strings to IST if from GeM portal, then convert to UTC
            dt_ist = dt.replace(tzinfo=IST_TZ)
            return dt_ist.astimezone(UTC_TZ)
        except ValueError:
            continue

    return None


def to_ist(dt: Optional[datetime]) -> Optional[datetime]:
    """Convert any aware datetime to Asia/Kolkata timezone."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC_TZ)
    return dt.astimezone(IST_TZ)


def format_ist_date(dt: Optional[datetime]) -> str:
    """Format as 'DD Mon YYYY' in IST (e.g., '16 Nov 2026')."""
    ist = to_ist(dt)
    if not ist:
        return "Not available from source"
    return ist.strftime("%d %b %Y")


def format_ist_time(dt: Optional[datetime]) -> str:
    """Format as 'hh:mm AM/PM' in IST (e.g., '03:00 PM')."""
    ist = to_ist(dt)
    if not ist:
        return "Not available from source"
    return ist.strftime("%I:%M %p")


def format_ist_full(dt: Optional[datetime]) -> str:
    """Format full IST string (e.g. '16 Nov 2026, 03:00 PM IST')."""
    ist = to_ist(dt)
    if not ist:
        return "Not available from source"
    return ist.strftime("%d %b %Y, %I:%M %p IST")


def compute_time_remaining(end_dt: Optional[datetime], now_utc: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Computes human-readable time remaining string and status flag.
    Returns:
    {
      "human": "5d 4h remaining" | "Closing in 2h 15m" | "Expired 3h ago" | "Not available",
      "is_expired": bool,
      "hours_left": float or None
    }
    """
    if not end_dt:
        return {
            "human": "Not available from source",
            "is_expired": False,
            "hours_left": None,
        }

    now = now_utc or datetime.now(UTC_TZ)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=UTC_TZ)

    diff = end_dt - now
    total_seconds = diff.total_seconds()

    if total_seconds <= 0:
        past_seconds = abs(total_seconds)
        past_hours = int(past_seconds // 3600)
        past_days = int(past_seconds // 86400)
        if past_days > 0:
            human = f"Expired {past_days}d ago"
        elif past_hours > 0:
            human = f"Expired {past_hours}h ago"
        else:
            human = "Expired just now"
        return {
            "human": human,
            "is_expired": True,
            "hours_left": 0.0,
        }

    hours = total_seconds / 3600.0
    days = int(total_seconds // 86400)
    rem_hours = int((total_seconds % 86400) // 3600)
    rem_mins = int((total_seconds % 3600) // 60)

    if days > 0:
        human = f"{days}d {rem_hours}h remaining"
    elif rem_hours > 0:
        human = f"Closing in {rem_hours}h {rem_mins}m"
    else:
        human = f"Closing in {rem_mins}m"

    return {
        "human": human,
        "is_expired": False,
        "hours_left": round(hours, 2),
    }
