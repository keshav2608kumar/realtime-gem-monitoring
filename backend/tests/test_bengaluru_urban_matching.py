"""
GeM BidWatch — Bengaluru Urban Strict Location & Category Matching Tests
Verifies the mandatory target location rules:
- Country: India
- State: Karnataka
- District: Bengaluru Urban
- City: Bengaluru (Bangalore)
- Strictly distinguishes Bengaluru Urban from Bengaluru Rural
- Prioritizes delivery/consignee location over buyer office
- Isolates ambiguous/unverified bids to Review queue
- Enforces the 7 GeM target product categories
"""
import pytest
from datetime import datetime, timezone, timedelta
from app.services.location_normalizer import (
    classify_bengaluru_urban,
    resolve_effective_bid_delivery_location,
    STATUS_VERIFIED_BENGALURU_URBAN,
    STATUS_VERIFIED_BENGALURU_RURAL,
    STATUS_PARTIALLY_VERIFIED,
    STATUS_AMBIGUOUS,
    STATUS_OUTSIDE_TARGET,
    STATUS_UNKNOWN,
)
from app.gem.filter_matcher import match_bid_to_profile
from app.schemas import BidCreate, ProfileOut
from app.services.category_service import TARGET_CATEGORIES


# ─── 1. CORE LOCATION CLASSIFICATION MATRIX ──────────────────────────────────

def test_bengaluru_urban_classification_matrix():
    """Verify all 9 mandatory test cases from requirements."""
    cases = [
        # (city, district, state, raw_text, expected_status)
        ("Bengaluru", "Bengaluru Urban", "KARNATAKA", None, STATUS_VERIFIED_BENGALURU_URBAN),
        ("Bangalore", "Bangalore Urban", "KARNATAKA", None, STATUS_VERIFIED_BENGALURU_URBAN),
        ("Bengaluru", "Bengaluru Rural", "KARNATAKA", None, STATUS_VERIFIED_BENGALURU_RURAL),
        ("Bangalore", "Bangalore Rural", "KARNATAKA", None, STATUS_VERIFIED_BENGALURU_RURAL),
        ("Bengaluru", "verified Bengaluru Urban district", "KARNATAKA", None, STATUS_VERIFIED_BENGALURU_URBAN),
        ("Mysuru", "Mysuru", "KARNATAKA", None, STATUS_OUTSIDE_TARGET),
        ("Jodhpur", "Jodhpur", "RAJASTHAN", None, STATUS_OUTSIDE_TARGET),
        ("Dehradun", "Dehradun", "UTTARAKHAND", None, STATUS_OUTSIDE_TARGET),
        ("Patna", "Patna", "BIHAR", None, STATUS_OUTSIDE_TARGET),
        ("Bangalore", None, None, "Bangalore, district unknown", STATUS_PARTIALLY_VERIFIED),
        (None, None, None, None, STATUS_UNKNOWN),
    ]

    for city, district, state, raw, expected in cases:
        status, conf, _, _, _ = classify_bengaluru_urban(
            city=city, district=district, state=state, raw_text=raw
        )
        assert status == expected, f"Failed for ({city}, {district}, {state}, {raw}): got {status}, expected {expected}"


def test_rural_towns_strictly_rejected():
    """Verify known Bengaluru Rural taluks/towns are ACCEPTED into Complete Bengaluru Region."""
    rural_towns = [
        "Doddaballapur", "Nelamangala", "Devanahalli",
        "Hoskote", "Kanakapura", "Ramanagara", "Magadi"
    ]
    for town in rural_towns:
        status, _, _, _, _ = classify_bengaluru_urban(
            city=town, state="KARNATAKA", raw_text=f"Delivery at {town} warehouse"
        )
        assert status == STATUS_VERIFIED_BENGALURU_RURAL, f"Rural town {town} should be accepted as VERIFIED_BENGALURU_RURAL"

    # Non-target Karnataka cities must be strictly rejected
    outside_ka_towns = ["Mysuru", "Hubli", "Dharwad", "Mangaluru", "Belagavi"]
    for town in outside_ka_towns:
        status, _, _, _, _ = classify_bengaluru_urban(
            city=town, state="KARNATAKA", raw_text=f"Delivery at {town} warehouse"
        )
        assert status == STATUS_OUTSIDE_TARGET, f"Non-target town {town} was not rejected"


def test_pincode_boundary_validation():
    """Verify Indian postal PIN codes: Urban (560001-560110) vs Rural (561000-562999) vs Outside."""
    # Urban PINs
    urban_pins = ["560001", "560012", "560037", "560068", "560100", "560110"]
    for pin in urban_pins:
        status, _, _, _, _ = classify_bengaluru_urban(pincode=pin)
        assert status == STATUS_VERIFIED_BENGALURU_URBAN, f"Urban PIN {pin} failed"

    # Rural PINs -> ACCEPTED in Complete Bengaluru Region
    rural_pins = ["562110", "562114", "561203"]
    for pin in rural_pins:
        status, _, _, _, _ = classify_bengaluru_urban(pincode=pin)
        assert status == STATUS_VERIFIED_BENGALURU_RURAL, f"Rural PIN {pin} should be accepted as VERIFIED_BENGALURU_RURAL"

    # Other States PINs -> REJECTED
    outside_pins = ["342001", "248001", "800001", "110001"]
    for pin in outside_pins:
        status, _, _, _, _ = classify_bengaluru_urban(pincode=pin)
        assert status == STATUS_OUTSIDE_TARGET, f"Outside PIN {pin} was not rejected"


# ─── 2. BUYER vs DELIVERY LOCATION SEPARATION ────────────────────────────────

def test_buyer_office_never_determines_delivery():
    """
    Priority rule:
    - Buyer: Bengaluru, Delivery: Jodhpur -> REJECT (OUTSIDE_TARGET)
    - Buyer: Jodhpur, Delivery: Bengaluru Urban -> MATCH (VERIFIED_BENGALURU_URBAN)
    - Buyer: New Delhi (HQ), Delivery: Bengaluru Urban in PDF -> MATCH (VERIFIED_BENGALURU_URBAN)
    """
    # 1. Buyer in Bengaluru, but delivery in Jodhpur
    bid_jodhpur_delivery = BidCreate(
        gem_bid_id=7001,
        bid_number="GEM/2026/B/7001",
        category_name="Computer Printer (V2)",
        category_key="COMPUTER_PRINTER_V2",
        buyer_state="KARNATAKA",
        buyer_city="Bengaluru",
        delivery_state="RAJASTHAN",
        delivery_city="Jodhpur",
        delivery_address="Air Force Station Jodhpur, Rajasthan",
    )
    status, _, _, _, _ = resolve_effective_bid_delivery_location(bid_jodhpur_delivery)
    assert status == STATUS_OUTSIDE_TARGET

    # 2. Buyer in Jodhpur, but delivery in Bengaluru Urban
    bid_bengaluru_delivery = BidCreate(
        gem_bid_id=7002,
        bid_number="GEM/2026/B/7002",
        category_name="Computer Printer (V2)",
        category_key="COMPUTER_PRINTER_V2",
        buyer_state="RAJASTHAN",
        buyer_city="Jodhpur",
        delivery_state="KARNATAKA",
        delivery_city="Bengaluru",
        delivery_district="Bengaluru Urban",
        delivery_address="DRDO Complex, CV Raman Nagar, Bengaluru Urban, Karnataka - 560093",
    )
    status, _, _, _, _ = resolve_effective_bid_delivery_location(bid_bengaluru_delivery)
    assert status == STATUS_VERIFIED_BENGALURU_URBAN

    # 3. Buyer in New Delhi HQ, PDF extracts delivery in Bengaluru Urban
    bid_pdf_delivery = BidCreate(
        gem_bid_id=7003,
        bid_number="GEM/2026/B/7003",
        category_name="High End Laptop - Notebook",
        category_key="HIGH_END_LAPTOP_NOTEBOOK",
        buyer_state="DELHI",
        buyer_city="New Delhi",
        pdf_delivery_state="KARNATAKA",
        pdf_delivery_city="Bengaluru",
        pdf_delivery_district="Bengaluru Urban",
        pdf_delivery_pincode="560012",
        pdf_delivery_address="Indian Institute of Science, Malleswaram, Bengaluru Urban, Karnataka 560012",
    )
    status, _, _, _, _ = resolve_effective_bid_delivery_location(bid_pdf_delivery)
    assert status == STATUS_VERIFIED_BENGALURU_URBAN


# ─── 3. STRICT PROFILE MATCHER ENFORCEMENT ───────────────────────────────────

def test_profile_matcher_strict_bengaluru_urban():
    profile = ProfileOut(
        id=1,
        name="Bengaluru Urban Radar",
        is_active=True,
        state="KARNATAKA",
        cities=["Bengaluru Urban", "Bangalore Urban", "Bengaluru"],
        categories=["TONER_INK_PRINTER_CONSUMABLES", "COMPUTER_PRINTER_V2"],
        created_at=datetime.now(timezone.utc),
    )

    # 1. Matching bid: Verified Bengaluru Urban & Matching Category
    bid_match = BidCreate(
        gem_bid_id=8001,
        bid_number="GEM/2026/B/8001",
        category_name="Toner Cartridges / Ink Cartridges / Consumables for Printers",
        category_key="TONER_INK_PRINTER_CONSUMABLES",
        consignee_state="KARNATAKA",
        consignee_city="Bengaluru",
        consignee_district="Bengaluru Urban",
        dept_name="ISRO Satellite Centre, Bengaluru",
    )
    res = match_bid_to_profile(bid_match, profile)
    assert res.matched is True

    # 2. Rejection: Outside location (Dehradun)
    bid_outside = BidCreate(
        gem_bid_id=8002,
        bid_number="GEM/2026/B/8002",
        category_name="Toner Cartridges / Ink Cartridges / Consumables for Printers",
        category_key="TONER_INK_PRINTER_CONSUMABLES",
        consignee_state="UTTARAKHAND",
        consignee_city="Dehradun",
        dept_name="Survey of India Dehradun",
    )
    res = match_bid_to_profile(bid_outside, profile)
    assert res.matched is False

    # 3. Rejection: Bengaluru Rural
    bid_rural = BidCreate(
        gem_bid_id=8003,
        bid_number="GEM/2026/B/8003",
        category_name="Computer Printer (V2)",
        category_key="COMPUTER_PRINTER_V2",
        consignee_state="KARNATAKA",
        consignee_city="Doddaballapur",
        consignee_district="Bengaluru Rural",
    )
    res = match_bid_to_profile(bid_rural, profile)
    assert res.matched is False

    # 4. Rejection: Ambiguous/District Unknown (Should NOT trigger alert)
    bid_unknown_dist = BidCreate(
        gem_bid_id=8004,
        bid_number="GEM/2026/B/8004",
        category_name="Computer Printer (V2)",
        category_key="COMPUTER_PRINTER_V2",
        raw_location_text="Bangalore, district unknown",
    )
    res = match_bid_to_profile(bid_unknown_dist, profile)
    assert res.matched is False


# ─── 4. SEVEN PRODUCT CATEGORIES INDEPENDENT & COMBINED TESTS ────────────────

def test_seven_product_categories_bengaluru_urban():
    """Verify all 7 product categories match when location is verified Bengaluru Urban."""
    for cat in TARGET_CATEGORIES:
        profile = ProfileOut(
            id=10,
            name=f"Profile for {cat.id}",
            is_active=True,
            state="KARNATAKA",
            cities=["Bengaluru"],
            categories=[cat.id],
            created_at=datetime.now(timezone.utc),
        )

        matching_bid = BidCreate(
            gem_bid_id=8500,
            bid_number="GEM/2026/B/8500",
            category_name=cat.display_name,
            category_key=cat.id,
            consignee_state="KARNATAKA",
            consignee_city="Bengaluru",
            consignee_district="Bengaluru Urban",
            dept_name="HAL Helicopter Division Bengaluru",
        )
        res = match_bid_to_profile(matching_bid, profile)
        assert res.matched is True, f"Failed for category {cat.id}"

    # Non-target category must NOT match even if in Bengaluru Urban
    profile_target = ProfileOut(
        id=20,
        name="Target Categories Only",
        is_active=True,
        state="KARNATAKA",
        cities=["Bengaluru"],
        categories=["SCANNER_V3"],
        created_at=datetime.now(timezone.utc),
    )
    non_target_bid = BidCreate(
        gem_bid_id=8501,
        bid_number="GEM/2026/B/8501",
        category_name="Executive Wooden Office Desk",
        consignee_state="KARNATAKA",
        consignee_city="Bengaluru",
        consignee_district="Bengaluru Urban",
    )
    res = match_bid_to_profile(non_target_bid, profile_target)
    assert res.matched is False


# ─── 5. API SCOPE FILTERING (MATCHING FEED vs REVIEW QUEUE) ─────────────────

def test_api_scope_and_stats(client):
    """
    Test:
    - /bids/?scope=bengaluru_urban returns only verified Bengaluru Urban bids
    - /bids/?scope=review returns ambiguous/unverified bids
    - /bids/?scope=outside returns outside target bids
    - /bids/summary/stats returns aggregated verification counts
    """
    now = datetime.now(timezone.utc)
    test_batch = [
        # 1. Verified Bengaluru Urban
        {
            "gem_bid_id": 9101,
            "bid_number": "GEM/2026/B/9101",
            "category_name": "Scanner (V3)",
            "consignee_state": "KARNATAKA",
            "consignee_city": "Bengaluru",
            "consignee_district": "Bengaluru Urban",
            "dept_name": "ISRO URSC Bengaluru",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=5)).isoformat(),
        },
        # 2. Outside Target (Dehradun)
        {
            "gem_bid_id": 9102,
            "bid_number": "GEM/2026/B/9102",
            "category_name": "Scanner (V3)",
            "consignee_state": "UTTARAKHAND",
            "consignee_city": "Dehradun",
            "dept_name": "ONGC Dehradun",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=5)).isoformat(),
        },
        # 3. Review Queue (district unknown)
        {
            "gem_bid_id": 9103,
            "bid_number": "GEM/2026/B/9103",
            "category_name": "High End Desktop Computer",
            "consignee_city": "Bangalore",
            "raw_location_text": "Bangalore, district unknown",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=5)).isoformat(),
        },
    ]

    r_sync = client.post("/bids/batch-sync", json=test_batch)
    assert r_sync.status_code == 201

    # Verified Bengaluru Urban feed
    r_urban = client.get("/bids/?scope=bengaluru_urban")
    assert r_urban.status_code == 200
    urban_bids = r_urban.json()
    urban_ids = [b["bid_number"] for b in urban_bids]
    assert "GEM/2026/B/9101" in urban_ids
    assert "GEM/2026/B/9102" not in urban_ids
    assert "GEM/2026/B/9103" not in urban_ids

    # Review Queue
    r_review = client.get("/bids/?scope=review")
    assert r_review.status_code == 200
    review_bids = r_review.json()
    review_ids = [b["bid_number"] for b in review_bids]
    assert "GEM/2026/B/9103" in review_ids
    assert "GEM/2026/B/9101" not in review_ids
    assert "GEM/2026/B/9102" not in review_ids

    # Outside Target
    r_outside = client.get("/bids/?scope=outside")
    assert r_outside.status_code == 200
    outside_bids = r_outside.json()
    outside_ids = [b["bid_number"] for b in outside_bids]
    assert "GEM/2026/B/9102" in outside_ids
    assert "GEM/2026/B/9101" not in outside_ids

    # Summary Stats
    r_stats = client.get("/bids/summary/stats")
    assert r_stats.status_code == 200
    stats = r_stats.json()
    assert stats["bengaluru_urban_verified"] >= 1
    assert stats["review_count"] >= 1
    assert stats["outside_target_count"] >= 1
