"""
GeM BidWatch — Bid Status & Expiry Classification Service
Enforces strict lifecycle states and guarantees expired bids do not pollute active feeds.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from zoneinfo import ZoneInfo
from app.services.datetime_service import to_ist, UTC_TZ, IST_TZ

# Standardized Bid Status Constants
STATUS_ACTIVE = "ACTIVE"
STATUS_CLOSING_SOON = "CLOSING_SOON"      # <= 24 hours remaining
STATUS_EXPIRING_TODAY = "EXPIRING_TODAY"  # Closes today in IST
STATUS_EXPIRED = "EXPIRED"                # Deadline has passed
STATUS_CANCELLED = "CANCELLED"            # Formally cancelled by buyer
STATUS_COMPLETED = "COMPLETED"            # Bid awarded / evaluated
STATUS_UNKNOWN = "UNKNOWN"                # Missing deadline / source error


def calculate_bid_status(
    end_date: Optional[datetime],
    raw_status: Optional[int] = None,
    now_utc: Optional[datetime] = None,
) -> str:
    """
    Calculate the authoritative bid status based on verified end date and source status.
    Uses timezone-aware comparisons. Never compares raw strings.
    """
    # 1. Check raw GeM status flags
    # In GeM: 0=Draft, 1=Active, 2=Cancelled, 3=Completed/Evaluated
    if raw_status == 2:
        return STATUS_CANCELLED
    if raw_status == 3:
        return STATUS_COMPLETED

    if not end_date:
        return STATUS_UNKNOWN

    now = now_utc or datetime.now(UTC_TZ)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=UTC_TZ)

    # 2. Check Expiry
    if end_date <= now:
        return STATUS_EXPIRED

    # 3. Time difference for active sub-states
    diff = end_date - now
    hours_left = diff.total_seconds() / 3600.0

    # 4. Check if expiring today in IST
    end_ist = to_ist(end_date)
    now_ist = to_ist(now)
    if end_ist and now_ist and end_ist.date() == now_ist.date():
        return STATUS_EXPIRING_TODAY

    if hours_left <= 24.0:
        return STATUS_CLOSING_SOON

    return STATUS_ACTIVE


def is_active_status(status_str: str) -> bool:
    """Returns True if status is considered an ongoing active bid opportunity."""
    return status_str in (STATUS_ACTIVE, STATUS_CLOSING_SOON, STATUS_EXPIRING_TODAY)
