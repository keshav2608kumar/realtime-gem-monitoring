"""
Comprehensive Tests for:
1. Feature 1: The 7 Exact GeM Product Categories (Filtering, Normalization, Multi-Select, Profile Matcher)
2. Feature 2: PDF Delivery Location Extraction Engine (Consignee Blocks, PIN Validation, Page Prioritization, Status Lifecycle)
"""
import pytest
from datetime import datetime, timezone, timedelta
from app.services.category_service import (
    match_category, get_all_target_categories, TARGET_CATEGORIES, CATEGORIES_BY_ID,
    is_valid_category_id, get_category_display_name
)
from app.services.pdf_location_extractor import (
    parse_consignee_block, extract_pincode, identify_state_from_text,
    identify_city_and_district, extract_location_from_pdf, ExtractedDeliveryLocation
)
from app.gem.filter_matcher import match_bid_to_profile
from app.schemas import BidCreate, ProfileOut
from app.models import Bid, Profile


# ─── 1. CATEGORY SERVICE & EXACT NAME TESTS ──────────────────────────────────

def test_seven_exact_categories_definitions():
    """Verify all seven categories exist with exact official names and stable IDs."""
    cats = get_all_target_categories()
    assert len(cats) == 7

    expected_categories = {
        "TONER_INK_PRINTER_CONSUMABLES": "Toner Cartridges / Ink Cartridges / Consumables for Printers",
        "SCANNER_V3": "Scanner (V3)",
        "A4_LEGAL_SIZE_MFP": "A4 and Legal Size Multifunction Printer (MFP)",
        "A3_SIZE_MFP": "A3 Size Multifunction Printer (MFP)",
        "COMPUTER_PRINTER_V2": "Computer Printer (V2)",
        "HIGH_END_DESKTOP": "High End Desktop Computer",
        "HIGH_END_LAPTOP_NOTEBOOK": "High End Laptop - Notebook",
    }

    for cat_id, expected_name in expected_categories.items():
        assert cat_id in CATEGORIES_BY_ID
        assert CATEGORIES_BY_ID[cat_id].display_name == expected_name
        assert is_valid_category_id(cat_id) is True
        assert get_category_display_name(cat_id) == expected_name


def test_category_matching_exact_and_aliases():
    """Verify exact match and canonical alias resolution."""
    # Exact canonical strings -> VERIFIED
    for cat in TARGET_CATEGORIES:
        k, name, status = match_category(cat.display_name)
        assert k == cat.id
        assert name == cat.display_name
        assert status == "VERIFIED"

    # Variations with extra descriptors -> MAPPED
    variations = [
        ("Computer Printer (V2) - Heavy Duty Departmental Duplex", "COMPUTER_PRINTER_V2"),
        ("A4 and Legal Size Multifunction Laser Printer (MFP) with ADF", "A4_LEGAL_SIZE_MFP"),
        ("A3 Size Multifunction Printer (MFP) Commercial Grade", "A3_SIZE_MFP"),
        ("Scanner (V3) Document High Speed", "SCANNER_V3"),
        ("High End Desktop Computer Graphic Workstation", "HIGH_END_DESKTOP"),
        ("High End Laptop - Notebook with 32GB RAM", "HIGH_END_LAPTOP_NOTEBOOK"),
        ("Toner Cartridges / Ink Cartridges / Consumables for Printers (OEM HP)", "TONER_INK_PRINTER_CONSUMABLES"),
    ]
    for text, expected_id in variations:
        k, name, status = match_category(text)
        assert k == expected_id, f"Failed on {text}"
        assert status == "MAPPED"


def test_category_matching_version_protection():
    """Ensure strict version separation: V1 does not match V2; non-V3 scanner does not match Scanner (V3)."""
    # Legacy printer V1 must NOT match Computer Printer (V2)
    k, _, status = match_category("Computer Printer (V1) Legacy")
    assert k is None
    assert status == "UNMAPPED"

    # General scanner without V3 must NOT falsely map to Scanner (V3)
    k, _, status = match_category("Medical Ultrasound Body Scanner")
    assert k is None
    assert status == "UNMAPPED"

    # Unrelated items must be UNMAPPED
    k, _, status = match_category("Hospital Beds and Surgical Instruments")
    assert k is None
    assert status == "UNMAPPED"

    # Empty or None category must be UNKNOWN
    k, _, status = match_category(None)
    assert k is None
    assert status == "UNKNOWN"

    k, _, status = match_category("   ")
    assert k is None
    assert status == "UNKNOWN"


def test_profile_matcher_with_category_filter():
    """Test that Profile matching engine enforces profile.categories correctly."""
    profile = ProfileOut(
        id=1,
        name="Printers & Scanners Watch",
        is_active=True,
        state="KARNATAKA",
        cities=["BANGALORE"],
        categories=["COMPUTER_PRINTER_V2", "SCANNER_V3"],
        created_at=datetime.now(timezone.utc),
    )

    # Bid 1: Computer Printer (V2) in Bangalore -> Should MATCH
    bid_matching = BidCreate(
        gem_bid_id=9001,
        bid_number="GEM/2026/B/9001",
        category_name="Computer Printer (V2) - Monochrome",
        category_key="COMPUTER_PRINTER_V2",
        consignee_state="KARNATAKA",
        consignee_city="Bangalore Urban",
        dept_name="ISRO Bangalore",
    )
    res = match_bid_to_profile(bid_matching, profile)
    assert res.matched is True
    assert "COMPUTER_PRINTER_V2" in res.match_reason

    # Bid 2: High End Laptop in Bangalore -> Should REJECT on category mismatch
    bid_wrong_cat = BidCreate(
        gem_bid_id=9002,
        bid_number="GEM/2026/B/9002",
        category_name="High End Laptop - Notebook",
        category_key="HIGH_END_LAPTOP_NOTEBOOK",
        consignee_state="KARNATAKA",
        consignee_city="Bangalore Urban",
        dept_name="ISRO Bangalore",
    )
    res = match_bid_to_profile(bid_wrong_cat, profile)
    assert res.matched is False
    assert "Category mismatch" in res.match_reason

    # Bid 3: Computer Printer (V2) in Jodhpur -> Should REJECT on state mismatch
    bid_wrong_loc = BidCreate(
        gem_bid_id=9003,
        bid_number="GEM/2026/B/9003",
        category_name="Computer Printer (V2)",
        category_key="COMPUTER_PRINTER_V2",
        consignee_state="RAJASTHAN",
        consignee_city="Jodhpur",
        dept_name="Military Station Jodhpur",
    )
    res = match_bid_to_profile(bid_wrong_loc, profile)
    assert res.matched is False
    assert "State mismatch" in res.match_reason


# ─── 2. PDF DELIVERY LOCATION EXTRACTION TESTS ───────────────────────────────

def test_pincode_extraction_and_state_mapping():
    """Verify 6-digit Indian PIN code extraction."""
    assert extract_pincode("Delivery to PIN 560017 near airport") == "560017"
    assert extract_pincode("Jodhpur Station 342005 Rajasthan") == "342005"
    assert extract_pincode("Virbhadra Road, Rishikesh - 249203") == "249203"
    assert extract_pincode("No pincode mentioned here") is None


def test_parse_consignee_block_full_table():
    """Verify parsing a standard GeM consignee/reporting officer table on final page."""
    sample_page = """
    Buyer Added Bid Specific Additional Terms and Conditions
    Consignees/Reporting Officer and Quantity
    S.No. Consignee/Reporting Officer Address Quantity Delivery Days
    1 Col. Rajesh Sharma 342005, Headquarters South Western Command, Military Station, Jodhpur, Rajasthan 15 30
    """
    loc = parse_consignee_block(sample_page, page_num=9, total_pages=9)
    assert loc is not None
    assert loc.city == "Jodhpur"
    assert loc.district == "Jodhpur"
    assert loc.state == "RAJASTHAN"
    assert loc.pincode == "342005"
    assert loc.verification_status == "VERIFIED"
    assert loc.confidence_score >= 0.85
    assert loc.page_number == 9
    assert loc.total_pages == 9
    assert "342005" in loc.full_address


def test_parse_consignee_block_alternate_format():
    """Verify parsing GeM delivery address with designation and institution."""
    sample_page = """
    Consignee / Delivery Address:
    Stores Officer
    All India Institute of Medical Sciences (AIIMS)
    Virbhadra Road, Rishikesh, Dehradun, Uttarakhand - 249203
    """
    loc = parse_consignee_block(sample_page, page_num=12, total_pages=12)
    assert loc is not None
    assert loc.state == "UTTARAKHAND"
    assert loc.pincode == "249203"
    assert loc.verification_status == "VERIFIED"


def test_parse_consignee_block_partial_address():
    """Verify partially verified address where city and state are present but PIN is missing."""
    sample_page = """
    Consignees/Reporting Officer:
    Executive Engineer, CPWD Division, Patna, Bihar
    """
    loc = parse_consignee_block(sample_page, page_num=5, total_pages=5)
    assert loc is not None
    assert loc.city == "Patna"
    assert loc.state == "BIHAR"
    assert loc.pincode is None
    assert loc.verification_status == "PARTIALLY_VERIFIED"


def test_extract_location_from_pdf_missing_or_corrupt():
    """Verify graceful handling when PDF bytes are missing, corrupt, or network unavailable."""
    res = extract_location_from_pdf(pdf_bytes=None, pdf_url=None, pdf_path="non_existent_file.pdf")
    assert res.verification_status == "PDF_UNAVAILABLE"
    assert "could not be verified" in res.full_address.lower()


# ─── 3. END-TO-END API TESTS ─────────────────────────────────────────────────

def test_api_list_categories(client):
    """Verify GET /bids/categories returns all seven official categories."""
    res = client.get("/bids/categories")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 7
    ids = [c["id"] for c in data]
    assert "TONER_INK_PRINTER_CONSUMABLES" in ids
    assert "SCANNER_V3" in ids
    assert "A4_LEGAL_SIZE_MFP" in ids
    assert "A3_SIZE_MFP" in ids
    assert "COMPUTER_PRINTER_V2" in ids
    assert "HIGH_END_DESKTOP" in ids
    assert "HIGH_END_LAPTOP_NOTEBOOK" in ids


def test_api_filter_by_single_category(client, db_session):
    """Test filtering bids by a single canonical category via API."""
    # Seed specific bids
    now = datetime.now(timezone.utc)
    b1 = Bid(
        gem_bid_id=9101,
        bid_number="GEM/2026/B/9101",
        category_name="Scanner (V3) Sheetfed",
        category_key="SCANNER_V3",
        category_mapping_status="VERIFIED",
        consignee_state="KARNATAKA",
        consignee_city="Bangalore Urban",
        end_date=now + timedelta(days=10),
        data_source_classification="LIVE_VERIFIED"
    )
    b2 = Bid(
        gem_bid_id=9102,
        bid_number="GEM/2026/B/9102",
        category_name="High End Desktop Computer Workstation",
        category_key="HIGH_END_DESKTOP",
        category_mapping_status="VERIFIED",
        consignee_state="KARNATAKA",
        consignee_city="Bangalore Urban",
        end_date=now + timedelta(days=10),
        data_source_classification="LIVE_VERIFIED"
    )
    db_session.add_all([b1, b2])
    db_session.commit()

    # Query for SCANNER_V3 only
    res = client.get("/bids/?categories=SCANNER_V3")
    assert res.status_code == 200
    bids = res.json()
    bid_numbers = [b["bid_number"] for b in bids]
    assert "GEM/2026/B/9101" in bid_numbers
    assert "GEM/2026/B/9102" not in bid_numbers


def test_api_filter_by_multiple_categories(client, db_session):
    """Test filtering bids by multiple categories simultaneously."""
    now = datetime.now(timezone.utc)
    b1 = Bid(
        gem_bid_id=9201,
        bid_number="GEM/2026/B/9201",
        category_name="Scanner (V3)",
        category_key="SCANNER_V3",
        consignee_state="KARNATAKA",
        end_date=now + timedelta(days=5),
    )
    b2 = Bid(
        gem_bid_id=9202,
        bid_number="GEM/2026/B/9202",
        category_name="High End Laptop - Notebook",
        category_key="HIGH_END_LAPTOP_NOTEBOOK",
        consignee_state="KARNATAKA",
        end_date=now + timedelta(days=5),
    )
    b3 = Bid(
        gem_bid_id=9203,
        bid_number="GEM/2026/B/9203",
        category_name="A3 Size Multifunction Printer (MFP)",
        category_key="A3_SIZE_MFP",
        consignee_state="KARNATAKA",
        end_date=now + timedelta(days=5),
    )
    db_session.add_all([b1, b2, b3])
    db_session.commit()

    # Filter for SCANNER_V3 and HIGH_END_LAPTOP_NOTEBOOK
    res = client.get("/bids/?categories=SCANNER_V3&categories=HIGH_END_LAPTOP_NOTEBOOK")
    assert res.status_code == 200
    bids = res.json()
    keys = {b["category_key"] for b in bids}
    assert "SCANNER_V3" in keys
    assert "HIGH_END_LAPTOP_NOTEBOOK" in keys
    assert "A3_SIZE_MFP" not in keys


def test_api_location_type_pdf_delivery_filter(client, db_session):
    """Test filtering by pdf_delivery location type."""
    now = datetime.now(timezone.utc)
    # Bid where buyer is in Delhi, but PDF extracted delivery location is in Jodhpur
    b = Bid(
        gem_bid_id=9301,
        bid_number="GEM/2026/B/9301",
        category_name="Computer Printer (V2)",
        category_key="COMPUTER_PRINTER_V2",
        buyer_city="New Delhi",
        buyer_state="DELHI",
        pdf_delivery_city="Jodhpur",
        pdf_delivery_state="RAJASTHAN",
        pdf_delivery_pincode="342005",
        pdf_verification_status="VERIFIED",
        end_date=now + timedelta(days=8),
    )
    db_session.add(b)
    db_session.commit()

    # Query with location_type=pdf_delivery and city=Jodhpur -> Should find it
    res = client.get("/bids/?location_type=pdf_delivery&city=Jodhpur")
    assert res.status_code == 200
    bids = res.json()
    assert any(x["bid_number"] == "GEM/2026/B/9301" for x in bids)

    # Query with location_type=buyer and city=Jodhpur -> Should NOT find it (buyer is Delhi)
    res_buyer = client.get("/bids/?location_type=buyer&city=Jodhpur")
    assert res_buyer.status_code == 200
    bids_buyer = res_buyer.json()
    assert not any(x["bid_number"] == "GEM/2026/B/9301" for x in bids_buyer)
