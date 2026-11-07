"""
Production Audit Tests: Corrigenda Date Override, PDF Location Extraction, and Bengaluru Urban Scoping.
"""
import os
import pytest
from datetime import datetime, timezone, timedelta

from app.models import Bid, Profile
from app.services.bid_status_service import calculate_bid_status, STATUS_ACTIVE, STATUS_EXPIRED
from app.services.location_normalizer import (
    resolve_effective_bid_delivery_location,
    STATUS_VERIFIED_BENGALURU_URBAN,
    STATUS_OUTSIDE_TARGET
)
from app.services.pdf_location_extractor import extract_location_from_pdf

# Search candidate paths for the downloaded official test PDF
CANDIDATE_PATHS = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "test_gem_9993172.pdf")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "test_gem_9993172.pdf")),
    "test_gem_9993172.pdf",
]
TEST_PDF_PATH = next((p for p in CANDIDATE_PATHS if os.path.exists(p)), None)


def test_official_pdf_location_extraction_page_3():
    """Verify that official GeM PDF for GEM/2026/B/8123875 extracts Bangalore Urban from page 3."""
    assert TEST_PDF_PATH is not None and os.path.exists(TEST_PDF_PATH), "test_gem_9993172.pdf must be present"

    result = extract_location_from_pdf(pdf_path=TEST_PDF_PATH)
    assert result.verification_status == "VERIFIED"
    assert result.confidence_score >= 0.85
    assert result.city in ("Bangalore", "Bengaluru")
    assert "Urban" in result.district
    assert result.state == "KARNATAKA"
    assert result.page_number == 3


def test_official_pdf_resolves_to_bengaluru_urban_target():
    """Verify extracted PDF delivery fields classify as STATUS_VERIFIED_BENGALURU_URBAN."""
    assert TEST_PDF_PATH is not None and os.path.exists(TEST_PDF_PATH), "test_gem_9993172.pdf must be present"

    extracted = extract_location_from_pdf(pdf_path=TEST_PDF_PATH)
    bid_dict = {
        "pdf_delivery_city": extracted.city,
        "pdf_delivery_district": extracted.district,
        "pdf_delivery_state": extracted.state,
        "pdf_delivery_address": extracted.full_address,
        "pdf_delivery_pincode": extracted.pincode,
        "consignee_city": "Bangalore Urban",
        "consignee_district": "Bangalore Urban",
        "consignee_state": "KARNATAKA",
    }
    status, conf, city, dist, state = resolve_effective_bid_delivery_location(bid_dict)
    assert status == STATUS_VERIFIED_BENGALURU_URBAN
    assert conf >= 0.90
    assert city == "Bengaluru"
    assert dist == "Bengaluru Urban"
    assert state == "KARNATAKA"


def test_placeholder_address_falls_back_to_consignee():
    """Verify placeholder failure string in pdf_delivery_address does not block Priority 3 consignee."""
    bid_dict = {
        "pdf_delivery_address": "Delivery address could not be verified from the available document.",
        "consignee_city": "Bangalore Urban",
        "consignee_district": "Bangalore Urban",
        "consignee_state": "KARNATAKA",
    }
    status, conf, city, dist, state = resolve_effective_bid_delivery_location(bid_dict)
    assert status == STATUS_VERIFIED_BENGALURU_URBAN
    assert conf >= 0.90
    assert city == "Bengaluru"
    assert dist == "Bengaluru Urban"


def test_corrigendum_date_override_keeps_bid_active():
    """
    Never treat original PDF deadline as final if a valid corrigendum changes it.
    If original deadline has expired, but revised deadline is in the future, status MUST be ACTIVE.
    """
    now = datetime.now(timezone.utc)
    original_past_deadline = now - timedelta(days=5)
    revised_future_deadline = now + timedelta(days=10)

    # Status using only original past date -> EXPIRED
    status_without_corrigendum = calculate_bid_status(original_past_deadline, 1, now_utc=now)
    assert status_without_corrigendum == STATUS_EXPIRED

    # Status using revised corrigendum deadline -> ACTIVE
    status_with_corrigendum = calculate_bid_status(revised_future_deadline, 1, now_utc=now)
    assert status_with_corrigendum == STATUS_ACTIVE


def test_corrigendum_both_deadlines_expired():
    """If both original and revised deadlines have passed, status is EXPIRED."""
    now = datetime.now(timezone.utc)
    original_past_deadline = now - timedelta(days=15)
    revised_past_deadline = now - timedelta(days=2)

    status = calculate_bid_status(revised_past_deadline, 1, now_utc=now)
    assert status == STATUS_EXPIRED


def test_api_bids_corrigendum_and_pdf_fields(client, db_session):
    """Verify API returns corrigendum fields and formatted IST dates for GEM/2026/B/8123875."""
    now = datetime.now(timezone.utc)
    orig_end = now - timedelta(days=2)
    rev_end = now + timedelta(days=12)

    test_bid = Bid(
        gem_bid_id=8123875,
        bid_number="GEM/2026/B/8123875",
        category_name="Computer Printer (V2)",
        category_key="COMPUTER_PRINTER_V2",
        category_mapping_status="VERIFIED",
        quantity=15,
        bid_type=1,
        status=1,
        dept_name="Indian Space Research Organization (ISRO Headquarters)",
        ministry_name="Department of Space",
        start_date=now - timedelta(days=10),
        original_end_date=orig_end,
        revised_end_date=rev_end,
        end_date=rev_end,
        corrigendum_status="EXTENDED",
        corrigendum_details="Deadline extended via official GeM Corrigendum No. 1",
        corrigendum_doc_url="https://bidplus.gem.gov.in/showbidDocument/9993172",
        date_source="OFFICIAL_CORRIGENDUM",
        consignee_state="KARNATAKA",
        consignee_city="Bengaluru",
        consignee_district="Bengaluru Urban",
        pdf_delivery_city="Bengaluru",
        pdf_delivery_district="Bengaluru Urban",
        pdf_delivery_state="KARNATAKA",
        pdf_delivery_address="Schedule 1: Location of Consignee: Bangalore Urban, Karnataka - ISRO Headquarters",
        pdf_delivery_pincode="560094",
        pdf_page_number=3,
        pdf_confidence_score=0.95,
        pdf_verification_status="VERIFIED",
        target_location_status=STATUS_VERIFIED_BENGALURU_URBAN,
        bid_url="https://bidplus.gem.gov.in/showbidDocument/9993172",
        data_source_classification="LIVE_VERIFIED"
    )
    db_session.add(test_bid)
    db_session.commit()

    response = client.get("/bids/?scope=bengaluru_urban&status=active&categories=COMPUTER_PRINTER_V2")
    assert response.status_code == 200
    bids = response.json()
    assert len(bids) > 0

    target = next((b for b in bids if b["bid_number"] == "GEM/2026/B/8123875"), None)
    assert target is not None
    assert target["target_location_status"] == STATUS_VERIFIED_BENGALURU_URBAN
    assert target["corrigendum_status"] == "EXTENDED"
    assert target["date_source"] == "OFFICIAL_CORRIGENDUM"
    assert "9993172" in target["bid_url"]
    assert target["original_end_date_formatted"] is not None
    assert target["revised_end_date_formatted"] is not None
    assert target["bid_status"] == STATUS_ACTIVE
