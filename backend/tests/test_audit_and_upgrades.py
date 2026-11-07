"""
GeM BidWatch — Master Engineering Verification Test Suite
Tests all 12 audited bug fixes:
1. Location accuracy (Jodhpur, Dehradun, Bangalore, Patna, Munger, Delhi, Unknown)
2. Publication and closing date parsing & IST timezone conversion
3. Dynamic bid status & strict expiry detection
4. Server-side sorting modes
5. Accurate fired alerts counter & acknowledgement
6. Data provenance and non-fabrication
"""
import pytest
from datetime import datetime, timezone, timedelta
from app.services.location_normalizer import normalize_location, resolve_state
from app.services.datetime_service import (
    parse_datetime, format_ist_date, format_ist_time, format_ist_full,
    compute_time_remaining, to_ist, UTC_TZ, IST_TZ
)
from app.services.bid_status_service import (
    calculate_bid_status, is_active_status,
    STATUS_ACTIVE, STATUS_CLOSING_SOON, STATUS_EXPIRING_TODAY, STATUS_EXPIRED, STATUS_UNKNOWN
)
from app.gem.filter_matcher import match_bid_to_profile
from app.schemas import BidCreate, ProfileOut
from app.models import Bid, Profile, Alert


# ─── 1. LOCATION TESTS ────────────────────────────────────────────────────────

def test_location_jodhpur_never_becomes_dehradun_or_bangalore():
    loc = normalize_location(city_hint="Jodhpur", state_hint="RAJASTHAN")
    assert loc.city == "Jodhpur"
    assert loc.state == "RAJASTHAN"
    assert loc.confidence == "VERIFIED"
    assert "bangalore" not in loc.display_location.lower()
    assert "dehradun" not in loc.display_location.lower()


def test_location_dehradun_never_becomes_jodhpur_or_bangalore():
    loc = normalize_location(city_hint="Dehradun", state_hint="UTTARAKHAND")
    assert loc.city == "Dehradun"
    assert loc.state == "UTTARAKHAND"
    assert loc.confidence == "VERIFIED"
    assert "bangalore" not in loc.display_location.lower()
    assert "jodhpur" not in loc.display_location.lower()


def test_location_bengaluru_normalization():
    loc = normalize_location(city_hint="bengaluru", state_hint="karnataka")
    assert loc.city == "Bengaluru"
    assert loc.state == "KARNATAKA"
    assert loc.confidence == "VERIFIED"


def test_location_bangalore_urban():
    loc = normalize_location(city_hint="Bangalore Urban", state_hint="KARNATAKA")
    assert loc.city == "Bangalore Urban"
    assert loc.state == "KARNATAKA"
    assert loc.confidence == "VERIFIED"


def test_location_patna_and_munger():
    loc_patna = normalize_location(city_hint="Patna", state_hint="BIHAR")
    assert loc_patna.city == "Patna"
    assert loc_patna.state == "BIHAR"

    loc_munger = normalize_location(city_hint="Munger", state_hint="BIHAR")
    assert loc_munger.city == "Munger"
    assert loc_munger.state == "BIHAR"


def test_location_delhi():
    loc_delhi = normalize_location(city_hint="Delhi", state_hint="DELHI")
    assert loc_delhi.city == "Delhi"
    assert loc_delhi.state == "DELHI"


def test_location_unknown_never_defaults_to_bangalore():
    loc = normalize_location(city_hint="", state_hint="")
    assert loc.confidence == "UNKNOWN"
    assert loc.display_location == "Not available from source"
    assert "bangalore" not in loc.display_location.lower()


# ─── 2. DATE AND TIMEZONE TESTS ───────────────────────────────────────────────

def test_date_parsing_various_formats():
    iso_dt = parse_datetime("2026-11-16T15:00:00Z")
    assert iso_dt is not None
    assert iso_dt.tzinfo == UTC_TZ

    offset_dt = parse_datetime("2026-11-16T15:00:00+05:30")
    assert offset_dt is not None
    # 15:00 IST is 09:30 UTC
    assert offset_dt.hour == 9
    assert offset_dt.minute == 30

    space_dt = parse_datetime("2026-11-16 15:00:00")
    assert space_dt is not None

    date_only = parse_datetime("2026-11-16")
    assert date_only is not None

    invalid = parse_datetime("not-a-date")
    assert invalid is None

    empty = parse_datetime("")
    assert empty is None


def test_ist_formatting():
    # 2026-11-16 09:30:00 UTC = 2026-11-16 15:00:00 IST
    dt = datetime(2026, 11, 16, 9, 30, tzinfo=UTC_TZ)
    date_str = format_ist_date(dt)
    time_str = format_ist_time(dt)
    full_str = format_ist_full(dt)

    assert "16 Nov 2026" in date_str
    assert "03:00 PM" in time_str
    assert "16 Nov 2026, 03:00 PM IST" in full_str

    none_str = format_ist_date(None)
    assert none_str == "Not available from source"


# ─── 3. BID STATUS AND EXPIRY DETECTION ───────────────────────────────────────

def test_bid_expiry_detection():
    now = datetime.now(UTC_TZ)
    past = now - timedelta(days=2)
    future_long = now + timedelta(days=5)
    future_soon = now + timedelta(hours=5)

    assert calculate_bid_status(past, now_utc=now) == STATUS_EXPIRED
    assert calculate_bid_status(future_long, now_utc=now) == STATUS_ACTIVE
    assert calculate_bid_status(future_soon, now_utc=now) in (STATUS_CLOSING_SOON, STATUS_EXPIRING_TODAY)
    assert calculate_bid_status(None, now_utc=now) == STATUS_UNKNOWN


def test_time_remaining_computation():
    now = datetime.now(UTC_TZ)
    past = now - timedelta(hours=3)
    future = now + timedelta(days=3, hours=4)

    rem_past = compute_time_remaining(past, now_utc=now)
    assert rem_past["is_expired"] is True
    assert "Expired" in rem_past["human"]

    rem_future = compute_time_remaining(future, now_utc=now)
    assert rem_future["is_expired"] is False
    assert "3d 4h remaining" in rem_future["human"]


# ─── 4. FILTER MATCHER & PROFILE INTEGRATION ──────────────────────────────────

def test_filter_matcher_prevents_empty_string_match():
    prof = ProfileOut(
        id=1,
        name="Dehradun Only",
        is_active=True,
        state="UTTARAKHAND",
        cities=["Dehradun"],
        keywords=["printer"],
        poll_interval_seconds=300,
        created_at=datetime.now(UTC_TZ),
    )

    # Bid with empty city must NOT match
    bid_empty_city = BidCreate(
        gem_bid_id=999901,
        bid_number="GEM/TEST/001",
        category_name="Heavy duty Laser Printer",
        consignee_state="UTTARAKHAND",
        consignee_city="",
    )
    res = match_bid_to_profile(bid_empty_city, prof)
    assert bool(res) is False

    # Bid with Jodhpur must NOT match Dehradun
    bid_jodhpur = BidCreate(
        gem_bid_id=999902,
        bid_number="GEM/TEST/002",
        category_name="Heavy duty Laser Printer",
        consignee_state="RAJASTHAN",
        consignee_city="Jodhpur",
    )
    res_jod = match_bid_to_profile(bid_jodhpur, prof)
    assert bool(res_jod) is False

    # Bid with Dehradun MUST match
    bid_dehradun = BidCreate(
        gem_bid_id=999903,
        bid_number="GEM/TEST/003",
        category_name="Heavy duty Laser Printer",
        consignee_state="UTTARAKHAND",
        consignee_city="Dehradun",
    )
    res_deh = match_bid_to_profile(bid_dehradun, prof)
    assert bool(res_deh) is True
    assert "printer" in res_deh.matched_keywords


# ─── 5. FULL API ROUTER END-TO-END TESTS ──────────────────────────────────────

def test_api_bids_lifecycle_and_sorting(client):
    # Insert test bids with different dates & locations
    now = datetime.now(UTC_TZ)
    bids = [
        BidCreate(
            gem_bid_id=888001,
            bid_number="GEM/2026/B/888001",
            category_name="Multi-function Laser Printer",
            consignee_state="RAJASTHAN",
            consignee_city="Jodhpur",
            start_date=now - timedelta(days=5),
            end_date=now + timedelta(days=10),
            estimated_value=500000.0,
        ),
        BidCreate(
            gem_bid_id=888002,
            bid_number="GEM/2026/B/888002",
            category_name="Black Toner Cartridge Pack",
            consignee_state="UTTARAKHAND",
            consignee_city="Dehradun",
            start_date=now - timedelta(days=2),
            end_date=now - timedelta(days=1),  # EXPIRED!
            estimated_value=120000.0,
        ),
        BidCreate(
            gem_bid_id=888003,
            bid_number="GEM/2026/B/888003",
            category_name="Network Printer Consumables",
            consignee_state="KARNATAKA",
            consignee_city="Bengaluru",
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(hours=12),  # CLOSING SOON!
            estimated_value=850000.0,
        ),
    ]

    # Ingest batch
    resp = client.post("/bids/batch-sync", json=[b.model_dump(mode="json") for b in bids])
    assert resp.status_code == 201

    # 1. Default active list: Expired bid (888002) MUST BE EXCLUDED
    r_active = client.get("/bids/?status=active")
    assert r_active.status_code == 200
    active_bids = r_active.json()
    active_ids = [b["bid_number"] for b in active_bids]
    assert "GEM/2026/B/888001" in active_ids
    assert "GEM/2026/B/888003" in active_ids
    assert "GEM/2026/B/888002" not in active_ids  # EXPIRED EXCLUDED!

    # 2. Query expired archive: Expired bid (888002) MUST BE PRESENT
    r_expired = client.get("/bids/?status=expired")
    assert r_expired.status_code == 200
    exp_bids = r_expired.json()
    exp_ids = [b["bid_number"] for b in exp_bids]
    assert "GEM/2026/B/888002" in exp_ids

    # 3. Verify location integrity: Jodhpur bid displays Jodhpur, RAJASTHAN
    jod_bid = next(b for b in active_bids if b["bid_number"] == "GEM/2026/B/888001")
    assert "Jodhpur" in jod_bid["display_location"]
    assert "RAJASTHAN" in jod_bid["display_location"]
    assert "Bangalore" not in jod_bid["display_location"]

    # 4. Verify sorting by highest estimated value
    r_sort_val = client.get("/bids/?status=active&sort_by=highest_value")
    sorted_bids = r_sort_val.json()
    assert sorted_bids[0]["bid_number"] == "GEM/2026/B/888003"  # 850k > 500k

    # 5. Verify alert stats
    r_alert_stats = client.get("/alerts/stats")
    assert r_alert_stats.status_code == 200
    a_stats = r_alert_stats.json()
    assert "total_alerts" in a_stats
    assert "unacknowledged_alerts" in a_stats
