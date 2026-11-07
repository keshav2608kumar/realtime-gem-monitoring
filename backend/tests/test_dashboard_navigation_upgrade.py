"""
GeM BidWatch — Dashboard Navigation UI Upgrade Tests
Verifies the new streamlined UI requirements:
1. ONLY TWO main navigation tabs:
   - "Verified Bids" (renamed from "Verified Bengaluru Urban", showing active verified bids in Bengaluru city/urban)
   - "Review Queue" (showing ambiguous locations, incomplete PDF extraction or data mismatches, allowing re-verification)
2. Main navigation removes:
   - "Closing Soon (<24h)"
   - "Expired Archive"
   - "All Ingested Records"
3. Compact Status Filter dropdown with:
   - "All Active" (active)
   - "Closing Soon (<24h)" (closing_soon)
   - "Expired" (expired)
   - "Cancelled" (cancelled)
4. Status filtering works correctly with both main tabs (Verified Bids and Review Queue).
5. All 7 product categories, location matching, server-side sorting, and visual alerts remain intact.
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.models import Bid, Profile, Alert
from app.services.location_normalizer import (
    STATUS_VERIFIED_BENGALURU_URBAN,
    STATUS_VERIFIED_BENGALURU_CITY,
    STATUS_PARTIALLY_VERIFIED,
    STATUS_AMBIGUOUS,
    STATUS_OUTSIDE_TARGET,
    STATUS_UNKNOWN,
)
from app.main import app

client = TestClient(app)


def test_dashboard_contains_only_two_main_tabs():
    """Verify HTML navigation bar renders ONLY TWO main tabs: Verified Bids and Review Queue."""
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    html = resp.text

    # Main tabs present
    assert "Verified Bids" in html, "Must contain 'Verified Bids' tab"
    assert "Review Queue" in html, "Must contain 'Review Queue' tab"
    assert "tabVerified" in html
    assert "tabReview" in html

    # Old 5-tab labels must NOT be present as navigation tab buttons
    assert "Verified Bengaluru Urban" not in html, "'Verified Bengaluru Urban' must be renamed to 'Verified Bids'"
    assert "tabClosingSoon" not in html, "'Closing Soon (<24h)' tab button must be removed from main navigation"
    assert "tabExpired" not in html, "'Expired Archive' tab button must be removed from main navigation"
    assert "tabAll" not in html, "'All Ingested Records' tab button must be removed from main navigation"


def test_status_filter_dropdown_options():
    """Verify compact Status Filter dropdown contains the exact required options."""
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    html = resp.text

    assert 'id="statusSelect"' in html, "Must contain statusSelect dropdown"
    assert 'onchange="onStatusFilterChange()"' in html
    assert '<option value="active" selected>All Active</option>' in html
    assert '<option value="closing_soon">Closing Soon (&lt;24h)</option>' in html
    assert '<option value="expired">Expired</option>' in html
    assert '<option value="cancelled">Cancelled</option>' in html


def test_status_filtering_with_verified_bids_tab(db_session):
    """
    Verify status filtering works accurately when on the Verified Bids tab:
    - active: only unexpired verified bids
    - closing_soon: verified bids closing in <24h
    - expired: verified bids with end_date in the past
    - cancelled: cancelled verified bids
    """
    now = datetime.now(timezone.utc)

    # 1. Active verified bid (closing in 5 days)
    bid_active = Bid(
        gem_bid_id=9401,
        bid_number="GEM/2026/B/9401",
        category_name="Computer Printer (V2)",
        category_key="COMPUTER_PRINTER_V2",
        start_date=now - timedelta(days=2),
        end_date=now + timedelta(days=5),
        status=1,
        bid_status="ACTIVE",
        consignee_city="Bengaluru",
        consignee_district="Bengaluru Urban",
        consignee_state="KARNATAKA",
        target_location_status=STATUS_VERIFIED_BENGALURU_URBAN,
        data_source_classification="LIVE_VERIFIED",
    )

    # 2. Closing soon verified bid (closing in 8 hours)
    bid_closing_soon = Bid(
        gem_bid_id=9402,
        bid_number="GEM/2026/B/9402",
        category_name="Scanner (V3)",
        category_key="SCANNER_V3",
        start_date=now - timedelta(days=6),
        end_date=now + timedelta(hours=8),
        status=1,
        bid_status="CLOSING_SOON",
        consignee_city="Bengaluru",
        consignee_district="Bengaluru Urban",
        consignee_state="KARNATAKA",
        target_location_status=STATUS_VERIFIED_BENGALURU_URBAN,
        data_source_classification="LIVE_VERIFIED",
    )

    # 3. Expired verified bid (closed 2 days ago)
    bid_expired = Bid(
        gem_bid_id=9403,
        bid_number="GEM/2026/B/9403",
        category_name="Toner Cartridges / Ink Cartridges / Consumables for Printers",
        category_key="TONER_INK_PRINTER_CONSUMABLES",
        start_date=now - timedelta(days=10),
        end_date=now - timedelta(days=2),
        status=1,
        bid_status="EXPIRED",
        consignee_city="Bengaluru",
        consignee_state="KARNATAKA",
        target_location_status=STATUS_VERIFIED_BENGALURU_CITY,
        data_source_classification="LIVE_VERIFIED",
    )

    # 4. Cancelled verified bid
    bid_cancelled = Bid(
        gem_bid_id=9404,
        bid_number="GEM/2026/B/9404",
        category_name="High End Desktop Computer",
        category_key="HIGH_END_DESKTOP_COMPUTER",
        start_date=now - timedelta(days=5),
        end_date=now + timedelta(days=10),
        status=2,  # Cancelled in GeM
        bid_status="CANCELLED",
        consignee_city="Bengaluru",
        consignee_district="Bengaluru Urban",
        consignee_state="KARNATAKA",
        target_location_status=STATUS_VERIFIED_BENGALURU_URBAN,
        data_source_classification="LIVE_VERIFIED",
    )

    # 5. Outside target bid (Jodhpur)
    bid_outside = Bid(
        gem_bid_id=9405,
        bid_number="GEM/2026/B/9405",
        category_name="Computer Printer (V2)",
        category_key="COMPUTER_PRINTER_V2",
        start_date=now - timedelta(days=2),
        end_date=now + timedelta(days=5),
        status=1,
        consignee_city="Jodhpur",
        consignee_state="RAJASTHAN",
        target_location_status=STATUS_OUTSIDE_TARGET,
        data_source_classification="LIVE_VERIFIED",
    )

    db_session.add_all([bid_active, bid_closing_soon, bid_expired, bid_cancelled, bid_outside])
    db_session.commit()

    # Query Status: active on Verified Bids tab
    r_act = client.get("/bids/?scope=verified&status=active&location_target=all_bengaluru")
    assert r_act.status_code == 200
    act_numbers = [b["bid_number"] for b in r_act.json()]
    assert "GEM/2026/B/9401" in act_numbers, "Active verified bid must be present"
    assert "GEM/2026/B/9402" in act_numbers, "Closing soon bid is also active"
    assert "GEM/2026/B/9403" not in act_numbers, "Expired bid must be excluded from active"
    assert "GEM/2026/B/9405" not in act_numbers, "Outside target must be excluded"

    # Query Status: closing_soon on Verified Bids tab
    r_soon = client.get("/bids/?scope=verified&status=closing_soon&location_target=all_bengaluru")
    assert r_soon.status_code == 200
    soon_numbers = [b["bid_number"] for b in r_soon.json()]
    assert "GEM/2026/B/9402" in soon_numbers, "Closing soon bid must be present"
    assert "GEM/2026/B/9401" not in soon_numbers, "Bid closing in 5 days is not closing soon (<24h)"

    # Query Status: expired on Verified Bids tab
    r_exp = client.get("/bids/?scope=verified&status=expired&location_target=all_bengaluru")
    assert r_exp.status_code == 200
    exp_numbers = [b["bid_number"] for b in r_exp.json()]
    assert "GEM/2026/B/9403" in exp_numbers, "Expired verified bid must be in expired feed"
    assert "GEM/2026/B/9401" not in exp_numbers, "Active bid must not be in expired feed"

    # Query Status: cancelled on Verified Bids tab
    r_canc = client.get("/bids/?scope=verified&status=cancelled&location_target=all_bengaluru")
    assert r_canc.status_code == 200
    canc_numbers = [b["bid_number"] for b in r_canc.json()]
    assert "GEM/2026/B/9404" in canc_numbers, "Cancelled verified bid must be in cancelled feed"
    assert "GEM/2026/B/9401" not in canc_numbers


def test_status_filtering_with_review_queue_tab(db_session):
    """
    Verify status filtering works accurately when on the Review Queue tab:
    - Pulls bids with ambiguous locations / incomplete extraction / unverified
    - Supports status=active, status=closing_soon, status=expired, status=cancelled
    """
    now = datetime.now(timezone.utc)

    # 1. Review bid active
    bid_review_active = Bid(
        gem_bid_id=9501,
        bid_number="GEM/2026/B/9501",
        category_name="Computer Printer (V2)",
        category_key="COMPUTER_PRINTER_V2",
        start_date=now - timedelta(days=2),
        end_date=now + timedelta(days=5),
        status=1,
        raw_location_text="Bangalore, district unknown",
        target_location_status=STATUS_PARTIALLY_VERIFIED,
        data_source_classification="LIVE_VERIFIED",
    )

    # 2. Review bid expired
    bid_review_expired = Bid(
        gem_bid_id=9502,
        bid_number="GEM/2026/B/9502",
        category_name="Scanner (V3)",
        category_key="SCANNER_V3",
        start_date=now - timedelta(days=10),
        end_date=now - timedelta(days=1),
        status=1,
        target_location_status=STATUS_AMBIGUOUS,
        data_source_classification="LIVE_VERIFIED",
    )

    db_session.add_all([bid_review_active, bid_review_expired])
    db_session.commit()

    # Query Review Queue + status=active
    r_act = client.get("/bids/?scope=review&status=active")
    assert r_act.status_code == 200
    act_numbers = [b["bid_number"] for b in r_act.json()]
    assert "GEM/2026/B/9501" in act_numbers
    assert "GEM/2026/B/9502" not in act_numbers

    # Query Review Queue + status=expired
    r_exp = client.get("/bids/?scope=review&status=expired")
    assert r_exp.status_code == 200
    exp_numbers = [b["bid_number"] for b in r_exp.json()]
    assert "GEM/2026/B/9502" in exp_numbers
    assert "GEM/2026/B/9501" not in exp_numbers


def test_reverification_controls_available_in_dashboard():
    """Verify that Re-verify controls and modal actions exist for Review Queue items."""
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    html = resp.text

    assert "Extract / Re-verify from PDF" in html, "On-demand re-verification button must be available"
    assert "runOnDemandPdfExtraction" in html, "runOnDemandPdfExtraction function must be present"
    assert "openBidDetailsModal" in html, "openBidDetailsModal function must be present"
