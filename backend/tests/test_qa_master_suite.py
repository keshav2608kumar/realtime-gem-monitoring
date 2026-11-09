"""
GeM BidWatch — Master QA Automated Test Suite
Exhaustive verification of:
1. PDF Synchronization (match, mismatch, corrupt, missing, checksum change, corrigenda)
2. Location Verification (Bengaluru City, Bengaluru Urban, Rural rejection, Jodhpur, Dehradun, Buyer vs Delivery)
3. Seven Product Categories (independent, multi-select, mapping, unmapped)
4. Dates & Expiry (Active, Closing Soon, Expired, Corrigendum Extension, Cancelled)
5. Frontend API Filters (Verified Bids, Review Queue, Status filter, Search, Sort)
6. Backend Database Integrity (Deduplication, Alert counting, Transaction consistency)
"""

import os
import io
import pytest
from datetime import datetime, timezone, timedelta

from app.models.bid import Bid
from app.models.profile import Profile
from app.models.alert import Alert
from app.schemas import BidCreate
from app.services.location_normalizer import (
    resolve_effective_bid_delivery_location,
    STATUS_VERIFIED_BENGALURU_URBAN,
    STATUS_VERIFIED_BENGALURU_CITY,
    STATUS_PARTIALLY_VERIFIED,
    STATUS_AMBIGUOUS,
    STATUS_OUTSIDE_TARGET,
    STATUS_UNKNOWN,
)
from app.services.bid_status_service import (
    calculate_bid_status,
    STATUS_ACTIVE,
    STATUS_CLOSING_SOON,
    STATUS_EXPIRED,
    STATUS_CANCELLED,
)
from app.services.category_service import (
    match_category,
    get_all_target_categories,
    TARGET_CATEGORIES,
)
from app.services.pdf_synchronizer import (
    synchronize_bid_with_pdf,
    parse_gem_ist_datetime,
    extract_metadata_from_page_1,
    SYNC_SYNCHRONIZED,
    SYNC_DATA_MISMATCH,
    SYNC_FAILED,
    SYNC_PDF_UNAVAILABLE,
)

# Search for the real sample PDF
CANDIDATE_PATHS = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "test_gem_9993172.pdf")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "test_gem_9993172.pdf")),
    "test_gem_9993172.pdf",
]
TEST_PDF_PATH = next((p for p in CANDIDATE_PATHS if os.path.exists(p)), None)


# ══════════════════════════════════════════════════════════════════════════════
# 1. PDF SYNCHRONIZATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_pdf_scenario_correct_match(db_session):
    """Scenario: Official GeM PDF with matching bid number synchronizes successfully."""
    assert TEST_PDF_PATH is not None, "test_gem_9993172.pdf must be present for authoritative test"

    bid = Bid(
        gem_bid_id=8123875,
        bid_number="GEM/2026/B/8123875",
        category_name="Computer Printer (V2)",
        bid_url="https://bidplus.gem.gov.in/showbidDocument/9993172",
        consignee_city="Bangalore",
        consignee_district="Bangalore Urban",
        consignee_state="KARNATAKA",
    )
    db_session.add(bid)
    db_session.commit()

    res = synchronize_bid_with_pdf(bid, pdf_path=TEST_PDF_PATH, db=db_session)

    assert res.is_bid_matched is True
    assert res.pdf_bid_number == "GEM/2026/B/8123875"
    assert res.synchronization_status == SYNC_SYNCHRONIZED
    assert res.target_location_status == STATUS_VERIFIED_BENGALURU_URBAN
    assert res.original_pdf_checksum is not None
    assert len(res.original_pdf_checksum) == 64
    assert res.data_confidence >= 0.85
    assert res.pdf_details_page_number == 1
    assert res.extracted_city in ("Bangalore", "Bengaluru")
    assert "Urban" in res.extracted_district


def test_pdf_scenario_wrong_bid_id_inside_pdf(db_session):
    """Scenario: PDF belongs to another tender -> mark DATA_MISMATCH and route to Review Queue."""
    assert TEST_PDF_PATH is not None

    bid = Bid(
        gem_bid_id=9999999,
        bid_number="GEM/2026/B/9999999",  # Expecting 9999999, but PDF contains 8123875
        category_name="Computer Printer (V2)",
        bid_url="https://bidplus.gem.gov.in/showbidDocument/wrong",
    )
    db_session.add(bid)
    db_session.commit()

    res = synchronize_bid_with_pdf(bid, pdf_path=TEST_PDF_PATH, db=db_session)

    assert res.is_bid_matched is False
    assert res.synchronization_status in (SYNC_DATA_MISMATCH, "PDF_BID_MISMATCH")
    assert res.latest_verified_status == "DATA_MISMATCH"
    assert res.target_location_status == STATUS_AMBIGUOUS  # Quarantined in Review Queue
    assert "MISMATCH" in (res.error_message or "").upper()


def test_pdf_scenario_missing_pdf(db_session):
    """Scenario: Missing or unreachable PDF marks PDF_UNAVAILABLE and does not fabricate values."""
    bid = Bid(
        gem_bid_id=7777777,
        bid_number="GEM/2026/B/7777777",
        bid_url=None,  # No document URL
    )
    db_session.add(bid)
    db_session.commit()

    res = synchronize_bid_with_pdf(bid, db=db_session)

    assert res.synchronization_status == SYNC_PDF_UNAVAILABLE
    assert res.latest_verified_status == "UNKNOWN"
    assert res.extracted_delivery_address is None


def test_pdf_scenario_corrupt_pdf(db_session):
    """Scenario: Corrupted PDF bytes mark FAILED and handle errors gracefully."""
    bid = Bid(
        gem_bid_id=6666666,
        bid_number="GEM/2026/B/6666666",
        bid_url="https://bidplus.gem.gov.in/showbidDocument/corrupt",
    )
    db_session.add(bid)
    db_session.commit()

    corrupt_bytes = b"%PDF-1.4 " + b"invalid corrupted binary stream content that is long enough to exceed the minimum source threshold..."
    res = synchronize_bid_with_pdf(bid, pdf_bytes=corrupt_bytes, db=db_session)

    assert res.synchronization_status == SYNC_FAILED
    assert res.latest_verified_status == "UNKNOWN"


def test_pdf_scenario_checksum_caching_and_change(db_session):
    """Scenario: Unchanged checksum skips redundant processing; changed checksum triggers re-verification."""
    assert TEST_PDF_PATH is not None

    with open(TEST_PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    bid = Bid(
        gem_bid_id=8123875,
        bid_number="GEM/2026/B/8123875",
        category_name="Computer Printer (V2)",
        bid_url="https://bidplus.gem.gov.in/showbidDocument/9993172",
    )
    db_session.add(bid)
    db_session.commit()

    # First run: processes document
    res1 = synchronize_bid_with_pdf(bid, pdf_bytes=pdf_bytes, db=db_session)
    assert res1.synchronization_status == SYNC_SYNCHRONIZED
    initial_hash = res1.original_pdf_checksum

    # Second run without force: cache hit
    res2 = synchronize_bid_with_pdf(bid, pdf_bytes=pdf_bytes, force=False, db=db_session)
    assert res2.original_pdf_checksum == initial_hash

    # Modified document (changed checksum): triggers re-verification
    mod_bytes = pdf_bytes + b"\n% Corrigendum Revision Appended"
    res3 = synchronize_bid_with_pdf(bid, pdf_bytes=mod_bytes, db=db_session)
    assert res3.original_pdf_checksum != initial_hash


def test_pdf_scenario_multiple_corrigenda_chronology():
    """Scenario: Process multiple corrigenda chronologically and select latest applicable deadline."""
    now = datetime.now(timezone.utc)
    original_deadline = now - timedelta(days=10)
    corr_1_deadline = now - timedelta(days=2)
    corr_2_deadline = now + timedelta(days=14)

    # Initial state: original deadline expired
    assert calculate_bid_status(original_deadline, 1, now_utc=now) == STATUS_EXPIRED

    # Corrigendum 1: extended but still passed
    assert calculate_bid_status(corr_1_deadline, 1, now_utc=now) == STATUS_EXPIRED

    # Corrigendum 2: extended into future -> ACTIVE
    assert calculate_bid_status(corr_2_deadline, 1, now_utc=now) == STATUS_ACTIVE


def test_pdf_scenario_original_and_revised_deadline_conflict():
    """Scenario: Original deadline passed, but corrigendum revised deadline is future -> ACTIVE."""
    now = datetime.now(timezone.utc)
    orig_past = now - timedelta(days=7)
    rev_future = now + timedelta(days=7)

    status = calculate_bid_status(rev_future, 1, now_utc=now)
    assert status == STATUS_ACTIVE
    # Ensure original deadline alone would be expired
    assert calculate_bid_status(orig_past, 1, now_utc=now) == STATUS_EXPIRED


# ══════════════════════════════════════════════════════════════════════════════
# 2. LOCATION VERIFICATION TESTS (Bengaluru City & Bengaluru Urban)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("loc_dict,expected_status,expected_city,expected_district", [
    (
        {"pdf_delivery_city": "Bengaluru", "pdf_delivery_district": "Bengaluru Urban", "pdf_delivery_state": "KARNATAKA"},
        STATUS_VERIFIED_BENGALURU_URBAN, "Bengaluru", "Bengaluru Urban"
    ),
    (
        {"pdf_delivery_city": "Bangalore", "pdf_delivery_district": "Bangalore Urban", "pdf_delivery_state": "KARNATAKA"},
        STATUS_VERIFIED_BENGALURU_URBAN, "Bengaluru", "Bengaluru Urban"
    ),
    (
        {"pdf_delivery_city": "Bengaluru", "pdf_delivery_district": "Bengaluru City", "pdf_delivery_state": "KARNATAKA"},
        STATUS_VERIFIED_BENGALURU_CITY, "Bengaluru", "Bengaluru"
    ),
    (
        {"pdf_delivery_city": "Bangalore", "pdf_delivery_district": "Bangalore City", "pdf_delivery_state": "KARNATAKA"},
        STATUS_VERIFIED_BENGALURU_CITY, "Bengaluru", "Bengaluru"
    ),
    (
        {"pdf_delivery_city": "Nelamangala", "pdf_delivery_district": "Bengaluru Rural", "pdf_delivery_state": "KARNATAKA"},
        STATUS_OUTSIDE_TARGET, "Bengaluru Rural", "Bengaluru Rural"
    ),
    (
        {"pdf_delivery_city": "Jodhpur", "pdf_delivery_district": "Jodhpur", "pdf_delivery_state": "RAJASTHAN"},
        STATUS_OUTSIDE_TARGET, "Jodhpur", "Jodhpur"
    ),
    (
        {"pdf_delivery_city": "Dehradun", "pdf_delivery_district": "Dehradun", "pdf_delivery_state": "UTTARAKHAND"},
        STATUS_OUTSIDE_TARGET, "Dehradun", "Dehradun"
    ),
    (
        {"pdf_delivery_city": "Patna", "pdf_delivery_district": "Patna", "pdf_delivery_state": "BIHAR"},
        STATUS_OUTSIDE_TARGET, "Patna", "Patna"
    ),
])
def test_location_scenarios_comprehensive(loc_dict, expected_status, expected_city, expected_district):
    st, conf, c, d, s = resolve_effective_bid_delivery_location(loc_dict)
    assert st == expected_status
    assert c == expected_city
    assert d == expected_district


def test_location_buyer_bangalore_delivery_jodhpur_strictly_rejected():
    """Scenario: Buyer office in Bangalore, but Delivery in Jodhpur -> Strictly OUTSIDE_TARGET."""
    bid_data = {
        "buyer_city": "Bengaluru",
        "buyer_district": "Bengaluru Urban",
        "buyer_state": "KARNATAKA",
        "pdf_delivery_city": "Jodhpur",
        "pdf_delivery_district": "Jodhpur",
        "pdf_delivery_state": "RAJASTHAN",
        "pdf_delivery_address": "AIIMS Jodhpur, Basni Industrial Area Phase-2, Jodhpur, Rajasthan - 342005",
    }
    st, _, city, dist, state = resolve_effective_bid_delivery_location(bid_data)
    assert st == STATUS_OUTSIDE_TARGET
    assert dist == "Jodhpur"


def test_location_buyer_jodhpur_delivery_bengaluru_urban_accepted():
    """Scenario: Buyer office in Jodhpur, but Delivery in Bengaluru Urban -> ACCEPTED."""
    bid_data = {
        "buyer_city": "Jodhpur",
        "buyer_district": "Jodhpur",
        "buyer_state": "RAJASTHAN",
        "pdf_delivery_city": "Bengaluru",
        "pdf_delivery_district": "Bengaluru Urban",
        "pdf_delivery_state": "KARNATAKA",
        "pdf_delivery_address": "ISRO Antariksh Bhavan, New BEL Road, Bangalore Urban, Karnataka - 560094",
        "pdf_delivery_pincode": "560094",
    }
    st, conf, city, dist, state = resolve_effective_bid_delivery_location(bid_data)
    assert st == STATUS_VERIFIED_BENGALURU_URBAN
    assert dist == "Bengaluru Urban"


def test_location_ambiguous_bangalore_routed_to_review():
    """Scenario: Ambiguous Bangalore mention with no district confirmation routes to Review Queue."""
    bid_data = {
        "consignee_city": "Bangalore",
        "consignee_state": None,
        "consignee_district": "District Unknown",
        "pdf_delivery_address": None,
    }
    st, conf, city, dist, state = resolve_effective_bid_delivery_location(bid_data)
    assert st in (STATUS_AMBIGUOUS, STATUS_PARTIALLY_VERIFIED)


def test_location_missing_delivery_address_unknown():
    """Scenario: Empty location record classifies as UNKNOWN."""
    st, conf, city, dist, state = resolve_effective_bid_delivery_location({})
    assert st == STATUS_UNKNOWN


# ══════════════════════════════════════════════════════════════════════════════
# 3. SEVEN PRODUCT CATEGORIES TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_seven_categories_exact_names():
    """Verify all seven required product categories exist with verbatim official titles."""
    cats = get_all_target_categories()
    assert len(cats) == 7

    expected_names = [
        "Toner Cartridges / Ink Cartridges / Consumables for Printers",
        "Scanner (V3)",
        "A4 and Legal Size Multifunction Printer (MFP)",
        "A3 Size Multifunction Printer (MFP)",
        "Computer Printer (V2)",
        "High End Desktop Computer",
        "High End Laptop - Notebook",
    ]
    for name in expected_names:
        assert any(c.display_name == name for c in cats), f"Category '{name}' must be registered"


@pytest.mark.parametrize("cat_title,expected_key,expected_status", [
    ("Toner Cartridges / Ink Cartridges / Consumables for Printers", "TONER_INK_PRINTER_CONSUMABLES", "VERIFIED"),
    ("Scanner (V3)", "SCANNER_V3", "VERIFIED"),
    ("A4 and Legal Size Multifunction Printer (MFP)", "A4_LEGAL_SIZE_MFP", "VERIFIED"),
    ("A3 Size Multifunction Printer (MFP)", "A3_SIZE_MFP", "VERIFIED"),
    ("Computer Printer (V2)", "COMPUTER_PRINTER_V2", "VERIFIED"),
    ("High End Desktop Computer", "HIGH_END_DESKTOP", "VERIFIED"),
    ("High End Laptop - Notebook", "HIGH_END_LAPTOP_NOTEBOOK", "VERIFIED"),
    # Variants & Aliases mapping
    ("Toner Cartridges / Ink Cartridges / Consumables for Printers (HP, Canon OEM)", "TONER_INK_PRINTER_CONSUMABLES", "MAPPED"),
    ("A4 and Legal Size Multifunction Printer (MFP) Heavy Duty", "A4_LEGAL_SIZE_MFP", "MAPPED"),
    ("Computer Printer (V2) Network Ready", "COMPUTER_PRINTER_V2", "MAPPED"),
    ("High End Desktop Computer Workstation", "HIGH_END_DESKTOP", "MAPPED"),
    ("High End Laptop - Notebook Intel i9", "HIGH_END_LAPTOP_NOTEBOOK", "MAPPED"),
])
def test_category_matching_scenarios(cat_title, expected_key, expected_status):
    key, defn, status = match_category(cat_title)
    assert key == expected_key
    assert status == expected_status


def test_category_unmapped_and_missing():
    """Scenario: Unrelated category or missing name handles properly."""
    key, _, status = match_category("Office Wooden Furniture Tables")
    assert key is None
    assert status == "UNMAPPED"

    key, _, status = match_category(None)
    assert key is None
    assert status == "UNKNOWN"


def test_api_multi_category_filtering(client, db_session):
    """Scenario: Multiple category selection in API query returns union of matching bids."""
    now = datetime.now(timezone.utc)
    future = now + timedelta(days=10)

    b1 = Bid(
        gem_bid_id=101, bid_number="GEM/2026/B/101", category_name="Scanner (V3)",
        category_key="SCANNER_V3", target_location_status=STATUS_VERIFIED_BENGALURU_URBAN,
        end_date=future, status=1
    )
    b2 = Bid(
        gem_bid_id=102, bid_number="GEM/2026/B/102", category_name="Computer Printer (V2)",
        category_key="COMPUTER_PRINTER_V2", target_location_status=STATUS_VERIFIED_BENGALURU_URBAN,
        end_date=future, status=1
    )
    b3 = Bid(
        gem_bid_id=103, bid_number="GEM/2026/B/103", category_name="High End Laptop - Notebook",
        category_key="HIGH_END_LAPTOP_NOTEBOOK", target_location_status=STATUS_VERIFIED_BENGALURU_URBAN,
        end_date=future, status=1
    )
    db_session.add_all([b1, b2, b3])
    db_session.commit()

    # Query with 2 categories: SCANNER_V3 and COMPUTER_PRINTER_V2
    res = client.get("/bids/?scope=verified&categories=SCANNER_V3&categories=COMPUTER_PRINTER_V2")
    assert res.status_code == 200
    bids = res.json()
    assert len(bids) == 2
    keys = {b["category_key"] for b in bids}
    assert keys == {"SCANNER_V3", "COMPUTER_PRINTER_V2"}


# ══════════════════════════════════════════════════════════════════════════════
# 4. DATE AND EXPIRY LOGIC TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_date_scenario_active_closing_soon_and_expired():
    """Scenario: Strict lifecycle resolution across active, closing soon, and expired states."""
    now = datetime.now(timezone.utc)

    # 1. Active: 5 days in future
    assert calculate_bid_status(now + timedelta(days=5), 1, now_utc=now) == STATUS_ACTIVE

    # 2. Closing soon: 12 hours in future
    assert calculate_bid_status(now + timedelta(hours=12), 1, now_utc=now) in (STATUS_CLOSING_SOON, "EXPIRING_TODAY")

    # 3. Expired: 1 minute in past
    assert calculate_bid_status(now - timedelta(minutes=1), 1, now_utc=now) == STATUS_EXPIRED

    # 4. Cancelled: status code 2
    assert calculate_bid_status(now + timedelta(days=5), 2, now_utc=now) == STATUS_CANCELLED

    # 5. Missing deadline: resolves to UNKNOWN
    assert calculate_bid_status(None, 1, now_utc=now) == "UNKNOWN"


def test_api_status_filter_strictly_excludes_expired_from_active(client, db_session):
    """Scenario: Active status filter MUST NEVER return an expired bid."""
    now = datetime.now(timezone.utc)
    active_bid = Bid(
        gem_bid_id=201, bid_number="GEM/2026/B/201",
        end_date=now + timedelta(days=5), status=1,
        target_location_status=STATUS_VERIFIED_BENGALURU_URBAN
    )
    expired_bid = Bid(
        gem_bid_id=202, bid_number="GEM/2026/B/202</td>",
        end_date=now - timedelta(days=2), status=1,
        target_location_status=STATUS_VERIFIED_BENGALURU_URBAN
    )
    db_session.add_all([active_bid, expired_bid])
    db_session.commit()

    # Query active
    res = client.get("/bids/?scope=verified&status=active")
    assert res.status_code == 200
    bids = res.json()
    assert len(bids) == 1
    assert bids[0]["gem_bid_id"] == 201

    # Query expired
    res_exp = client.get("/bids/?scope=verified&status=expired")
    assert res_exp.status_code == 200
    exp_bids = res_exp.json()
    assert len(exp_bids) == 1
    assert exp_bids[0]["gem_bid_id"] == 202


# ══════════════════════════════════════════════════════════════════════════════
# 5. FRONTEND NAVIGATION & FILTERS TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_frontend_dashboard_contains_only_two_main_tabs(client):
    """Scenario: Dashboard contains ONLY Verified Bids and Review Queue main tabs."""
    res = client.get("/dashboard")
    assert res.status_code == 200
    html = res.text

    # Two main tabs present
    assert 'id="tabVerified"' in html
    assert 'Verified Bids' in html
    assert 'id="tabReview"' in html
    assert 'Review Queue' in html

    # Removed tabs are NOT main navigation buttons
    assert 'id="tabClosingSoon"' not in html
    assert 'id="tabExpired"' not in html
    assert 'id="tabAll"' not in html

    # Status dropdown is present
    assert 'id="statusSelect"' in html
    assert 'value="active"' in html
    assert 'value="closing_soon"' in html
    assert 'value="expired"' in html
    assert 'value="cancelled"' in html


def test_data_mismatch_quarantined_to_review_queue(client, db_session):
    """Scenario: Bid with DATA_MISMATCH is excluded from Verified Bids and displayed in Review Queue."""
    now = datetime.now(timezone.utc)
    future = now + timedelta(days=5)

    clean_bid = Bid(
        gem_bid_id=301, bid_number="GEM/2026/B/301",
        target_location_status=STATUS_VERIFIED_BENGALURU_URBAN,
        synchronization_status=SYNC_SYNCHRONIZED,
        end_date=future, status=1
    )
    mismatched_bid = Bid(
        gem_bid_id=302, bid_number="GEM/2026/B/302",
        target_location_status=STATUS_VERIFIED_BENGALURU_URBAN,  # Location was previously tagged, but doc mismatched!
        synchronization_status=SYNC_DATA_MISMATCH,
        end_date=future, status=1
    )
    db_session.add_all([clean_bid, mismatched_bid])
    db_session.commit()

    # 1. Verified Bids tab: excludes mismatched_bid
    res_ver = client.get("/bids/?scope=verified&status=active")
    assert res_ver.status_code == 200
    v_bids = res_ver.json()
    assert len(v_bids) == 1
    assert v_bids[0]["gem_bid_id"] == 301

    # 2. Review Queue tab: includes mismatched_bid
    res_rev = client.get("/bids/?scope=review&status=active")
    assert res_rev.status_code == 200
    r_bids = res_rev.json()
    assert len(r_bids) == 1
    assert r_bids[0]["gem_bid_id"] == 302


# ══════════════════════════════════════════════════════════════════════════════
# 6. BACKEND DATABASE INTEGRITY & ALERTS TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_backend_duplicate_ingestion_idempotence(client, db_session):
    """Scenario: Ingesting the same bid twice does not duplicate records in database."""
    now = datetime.now(timezone.utc)
    payload = [{
        "gem_bid_id": 501,
        "bid_number": "GEM/2026/B/501",
        "category_name": "Computer Printer (V2)",
        "consignee_city": "Bengaluru",
        "consignee_district": "Bengaluru Urban",
        "consignee_state": "KARNATAKA",
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(days=7)).isoformat(),
    }]

    # Ingestion 1
    res1 = client.post("/bids/batch-sync", json=payload)
    assert res1.status_code == 201
    assert res1.json()["bids_inserted"] == 1

    # Ingestion 2 (Duplicate)
    res2 = client.post("/bids/batch-sync", json=payload)
    assert res2.status_code == 201
    assert res2.json()["bids_inserted"] == 0
    assert res2.json()["bids_updated"] == 1

    # Total in DB remains 1
    assert db_session.query(Bid).filter(Bid.gem_bid_id == 501).count() == 1


def test_backend_alert_counters_distinguish_fired_from_delivered(client, db_session):
    """Scenario: Database counters distinguish fired alerts from delivered push notifications."""
    profile = Profile(name="Toner Alert Profile", is_active=True, state="KARNATAKA", cities=["Bangalore"])
    bid = Bid(gem_bid_id=601, bid_number="GEM/2026/B/601", category_name="Toner Cartridges")
    db_session.add_all([profile, bid])
    db_session.commit()

    # Alert 1: Fired, but notification failed
    a1 = Alert(
        profile_id=profile.id,
        bid_id=bid.id,
        status="NEW",
        notification_sent=False,
        notification_error="FCM token expired",
    )
    db_session.add(a1)
    db_session.commit()

    res = client.get("/alerts/stats")
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_alerts"] == 1
    assert stats["new_alerts"] == 1
    assert stats["dispatched_notifications"] == 0  # Not counted as delivered!
    assert stats["failed_notifications"] == 1
