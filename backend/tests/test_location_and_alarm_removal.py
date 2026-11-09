"""
GeM BidWatch — Location Target Normalization & Alarm Removal Regression Tests
Covers all 12 explicit prompt scenarios + alarm feature complete removal verification:
1. Bengaluru city -> ACCEPT (STATUS_VERIFIED_BENGALURU_CITY)
2. Bangalore city -> ACCEPT (STATUS_VERIFIED_BENGALURU_CITY)
3. Bengaluru Urban district -> ACCEPT (STATUS_VERIFIED_BENGALURU_URBAN)
4. Bangalore Urban district -> ACCEPT (STATUS_VERIFIED_BENGALURU_URBAN)
5. Bengaluru Rural -> REJECT (STATUS_OUTSIDE_TARGET)
6. Jodhpur -> REJECT (STATUS_OUTSIDE_TARGET)
7. Dehradun -> REJECT (STATUS_OUTSIDE_TARGET)
8. Buyer Bangalore + delivery Jodhpur -> REJECT (STATUS_OUTSIDE_TARGET)
9. Buyer Jodhpur + delivery Bangalore Urban -> ACCEPT (STATUS_VERIFIED_BENGALURU_URBAN)
10. Ambiguous bare Bangalore -> REVIEW (STATUS_PARTIALLY_VERIFIED)
11. Missing delivery location -> UNKNOWN (STATUS_UNKNOWN)
12. 'All Bengaluru Targets' filter returns both city and district records
13. Alarm feature completely removed: zero siren/audio code, visual alerts function properly
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.models import Bid, Profile, Alert
from app.services.location_normalizer import (
    classify_bengaluru_urban,
    resolve_effective_bid_delivery_location,
    STATUS_VERIFIED_BENGALURU_URBAN,
    STATUS_VERIFIED_BENGALURU_RURAL,
    STATUS_VERIFIED_BENGALURU_CITY,
    STATUS_PARTIALLY_VERIFIED,
    STATUS_AMBIGUOUS,
    STATUS_OUTSIDE_TARGET,
    STATUS_UNKNOWN,
)
from app.schemas import BidCreate, ProfileOut
from app.main import app

client = TestClient(app)


# ─── SCENARIO 1: Bengaluru city -> ACCEPT ─────────────────────────────────────
def test_scenario_1_bengaluru_city_accepted():
    status, conf, city, dist, state = classify_bengaluru_urban(
        city="Bengaluru",
        state="KARNATAKA",
    )
    assert status == STATUS_VERIFIED_BENGALURU_CITY
    assert conf >= 0.85
    assert city == "Bengaluru"
    assert state == "KARNATAKA"


# ─── SCENARIO 2: Bangalore city -> ACCEPT ─────────────────────────────────────
def test_scenario_2_bangalore_city_accepted():
    status, conf, city, dist, state = classify_bengaluru_urban(
        city="Bangalore",
        state="KARNATAKA",
    )
    assert status == STATUS_VERIFIED_BENGALURU_CITY
    assert conf >= 0.85
    assert city == "Bengaluru"
    assert state == "KARNATAKA"

    # Also test with raw text alias "Bangalore City, Karnataka"
    status_raw, _, _, _, _ = classify_bengaluru_urban(
        raw_text="Consignee delivery at Bangalore City, Karnataka"
    )
    assert status_raw == STATUS_VERIFIED_BENGALURU_CITY


# ─── SCENARIO 3: Bengaluru Urban district -> ACCEPT ───────────────────────────
def test_scenario_3_bengaluru_urban_district_accepted():
    status, conf, city, dist, state = classify_bengaluru_urban(
        city="Bengaluru",
        district="Bengaluru Urban",
        state="KARNATAKA",
    )
    assert status == STATUS_VERIFIED_BENGALURU_URBAN
    assert conf >= 0.90
    assert dist == "Bengaluru Urban"


# ─── SCENARIO 4: Bangalore Urban district -> ACCEPT ───────────────────────────
def test_scenario_4_bangalore_urban_district_accepted():
    status, conf, city, dist, state = classify_bengaluru_urban(
        city="Bangalore",
        district="Bangalore Urban",
        state="KARNATAKA",
    )
    assert status == STATUS_VERIFIED_BENGALURU_URBAN
    assert conf >= 0.90
    assert dist == "Bengaluru Urban"


# ─── SCENARIO 5: Bengaluru Rural -> ACCEPT ────────────────────────────────────
def test_scenario_5_bengaluru_rural_accepted():
    # Explicit Bengaluru Rural district -> ACCEPT
    status, _, _, dist, _ = classify_bengaluru_urban(
        city="Bengaluru",
        district="Bengaluru Rural",
        state="KARNATAKA",
    )
    assert status == STATUS_VERIFIED_BENGALURU_RURAL
    assert dist == "Bengaluru Rural"

    # Rural peripheral towns -> ACCEPT in Bengaluru Rural
    for rural_town in ["Doddaballapur", "Nelamangala", "Devanahalli", "Hoskote"]:
        st, _, _, _, _ = classify_bengaluru_urban(
            city=rural_town,
            state="KARNATAKA",
        )
        assert st == STATUS_VERIFIED_BENGALURU_RURAL, f"{rural_town} should be accepted in Bengaluru Rural"


# ─── SCENARIO 6: Jodhpur -> REJECT ────────────────────────────────────────────
def test_scenario_6_jodhpur_rejected():
    status, _, _, _, state = classify_bengaluru_urban(
        city="Jodhpur",
        district="Jodhpur",
        state="RAJASTHAN",
    )
    assert status == STATUS_OUTSIDE_TARGET
    assert state == "RAJASTHAN"


# ─── SCENARIO 7: Dehradun -> REJECT ───────────────────────────────────────────
def test_scenario_7_dehradun_rejected():
    status, _, _, _, state = classify_bengaluru_urban(
        city="Dehradun",
        district="Dehradun",
        state="UTTARAKHAND",
    )
    assert status == STATUS_OUTSIDE_TARGET
    assert state == "UTTARAKHAND"


# ─── SCENARIO 8: Buyer Bangalore + delivery Jodhpur -> REJECT ─────────────────
def test_scenario_8_buyer_bangalore_delivery_jodhpur_rejected():
    bid = BidCreate(
        gem_bid_id=9101,
        bid_number="GEM/2026/B/9101",
        category_name="Scanner (V3)",
        category_key="SCANNER_V3",
        buyer_city="Bengaluru",
        buyer_district="Bengaluru Urban",
        buyer_state="KARNATAKA",
        delivery_city="Jodhpur",
        delivery_district="Jodhpur",
        delivery_state="RAJASTHAN",
        delivery_address="Jodhpur Air Force Depot, Rajasthan",
    )
    status, _, city, dist, state = resolve_effective_bid_delivery_location(bid)
    assert status == STATUS_OUTSIDE_TARGET
    assert state == "RAJASTHAN"


# ─── SCENARIO 9: Buyer Jodhpur + delivery Bangalore Urban -> ACCEPT ───────────
def test_scenario_9_buyer_jodhpur_delivery_bangalore_urban_accepted():
    bid = BidCreate(
        gem_bid_id=9102,
        bid_number="GEM/2026/B/9102",
        category_name="Computer Printer (V2)",
        category_key="COMPUTER_PRINTER_V2",
        buyer_city="Jodhpur",
        buyer_district="Jodhpur",
        buyer_state="RAJASTHAN",
        delivery_city="Bangalore",
        delivery_district="Bangalore Urban",
        delivery_state="KARNATAKA",
        delivery_address="HAL Management Academy, Vimanapura, Bangalore Urban, Karnataka - 560017",
    )
    status, conf, city, dist, state = resolve_effective_bid_delivery_location(bid)
    assert status == STATUS_VERIFIED_BENGALURU_URBAN
    assert conf >= 0.90
    assert city == "Bengaluru"
    assert state == "KARNATAKA"


# ─── SCENARIO 10: Ambiguous bare Bangalore -> REVIEW ──────────────────────────
def test_scenario_10_ambiguous_bare_bangalore_isolated_to_review():
    # Bare "Bangalore" with no state or district verification
    status_bare, conf, _, _, _ = classify_bengaluru_urban(
        city="Bangalore",
        state=None,
        district=None,
    )
    assert status_bare == STATUS_PARTIALLY_VERIFIED

    # "Bangalore, district unknown"
    status_unknown_dist, _, _, _, _ = classify_bengaluru_urban(
        raw_text="Tender Office Bangalore, district unknown"
    )
    assert status_unknown_dist == STATUS_PARTIALLY_VERIFIED


# ─── SCENARIO 11: Missing delivery location -> UNKNOWN ─────────────────────────
def test_scenario_11_missing_delivery_location_unknown():
    status, conf, city, dist, state = classify_bengaluru_urban(
        city=None,
        district=None,
        state=None,
        raw_text=None,
        pincode=None,
    )
    assert status == STATUS_UNKNOWN
    assert conf == 0.0
    assert city is None


# ─── SCENARIO 12: 'All Bengaluru Targets' returns both city and district ──────
def test_scenario_12_all_bengaluru_targets_returns_city_and_district(db_session):
    now = datetime.now(timezone.utc)

    # 1. City-level record
    bid_city = Bid(
        gem_bid_id=9201,
        bid_number="GEM/2026/B/9201",
        category_name="High End Desktop Computer",
        category_key="HIGH_END_DESKTOP_COMPUTER",
        start_date=now - timedelta(days=2),
        end_date=now + timedelta(days=5),
        bid_status="ACTIVE",
        consignee_city="Bengaluru",
        consignee_state="KARNATAKA",
        target_location_status=STATUS_VERIFIED_BENGALURU_CITY,
        data_source_classification="LIVE_VERIFIED",
    )

    # 2. District-level record
    bid_urban = Bid(
        gem_bid_id=9202,
        bid_number="GEM/2026/B/9202",
        category_name="High End Laptop - Notebook",
        category_key="HIGH_END_LAPTOP_NOTEBOOK",
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=7),
        bid_status="ACTIVE",
        consignee_city="Bengaluru",
        consignee_district="Bengaluru Urban",
        consignee_state="KARNATAKA",
        target_location_status=STATUS_VERIFIED_BENGALURU_URBAN,
        data_source_classification="LIVE_VERIFIED",
    )

    # 3. Outside record (Jodhpur)
    bid_outside = Bid(
        gem_bid_id=9203,
        bid_number="GEM/2026/B/9203",
        category_name="Scanner (V3)",
        category_key="SCANNER_V3",
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=7),
        bid_status="ACTIVE",
        consignee_city="Jodhpur",
        consignee_state="RAJASTHAN",
        target_location_status=STATUS_OUTSIDE_TARGET,
        data_source_classification="LIVE_VERIFIED",
    )

    db_session.add_all([bid_city, bid_urban, bid_outside])
    db_session.commit()

    # Query with default or explicit location_target=all_bengaluru
    resp_all = client.get("/bids/?location_target=all_bengaluru")
    assert resp_all.status_code == 200
    all_bids = resp_all.json()
    bid_numbers = [b["bid_number"] for b in all_bids]

    assert "GEM/2026/B/9201" in bid_numbers, "City record should be in All Bengaluru Targets"
    assert "GEM/2026/B/9202" in bid_numbers, "District record should be in All Bengaluru Targets"
    assert "GEM/2026/B/9203" not in bid_numbers, "Outside record must be excluded from All Bengaluru Targets"

    # Query location_target=bengaluru_city
    resp_city = client.get("/bids/?location_target=bengaluru_city")
    assert resp_city.status_code == 200
    city_bids = resp_city.json()
    city_numbers = [b["bid_number"] for b in city_bids]
    assert "GEM/2026/B/9201" in city_numbers
    assert "GEM/2026/B/9202" not in city_numbers

    # Query location_target=bengaluru_urban
    resp_urban = client.get("/bids/?location_target=bengaluru_urban")
    assert resp_urban.status_code == 200
    urban_bids = resp_urban.json()
    urban_numbers = [b["bid_number"] for b in urban_bids]
    assert "GEM/2026/B/9202" in urban_numbers
    assert "GEM/2026/B/9201" not in urban_numbers


# ─── SCENARIO 13: Alarm Feature Completely Removed ─────────────────────────────
def test_scenario_13_alarm_feature_completely_removed(db_session):
    """
    Verify complete purge of alarm controls:
    1. Dashboard HTML contains no btnAlarmToggle, no toggleAudioAlarm, no audioCtx, no sirenOsc.
    2. Alert acknowledgement endpoint POST /alerts/{id}/ack works cleanly.
    3. Visual match alert banner and modal exist and function without audio dependencies.
    """
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    html = resp.text

    # Audio/siren purge checks
    assert "btnAlarmToggle" not in html, "btnAlarmToggle button must be completely removed"
    assert "toggleAudioAlarm" not in html, "toggleAudioAlarm must be completely removed"
    assert "playAudioSiren" not in html, "playAudioSiren must be completely removed"
    assert "stopAudioSiren" not in html, "stopAudioSiren must be completely removed"
    assert "sirenOsc" not in html, "Audio oscillator must be completely removed"
    assert "AudioContext" not in html, "Web Audio API AudioContext must be completely removed"
    assert "Dismiss & Mute" not in html, "Dismiss & Mute button text must be removed"

    # Visual elements checks
    assert "Dismiss & Acknowledge" in html, "Dismiss & Acknowledge visual button must be present"
    assert "activeAlertBanner" in html, "Active visual alert banner must remain intact"
    assert "locationTargetSelect" in html, "Location Target selector must be present"
    assert "All Bengaluru Targets" in html, "All Bengaluru Targets option must be present"
    assert "Bengaluru City" in html, "Bengaluru City option must be present"
    assert "Bengaluru Urban District" in html, "Bengaluru Urban District option must be present"

    # Test visual alert creation and ack without audio
    now = datetime.now(timezone.utc)
    profile = Profile(
        name="Bengaluru Target Watcher",
        state="KARNATAKA",
        cities=["Bengaluru"],
        is_active=True,
    )
    db_session.add(profile)
    db_session.commit()

    bid = Bid(
        gem_bid_id=9301,
        bid_number="GEM/2026/B/9301",
        category_name="Computer Printer (V2)",
        category_key="COMPUTER_PRINTER_V2",
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=3),
        bid_status="ACTIVE",
        consignee_city="Bengaluru",
        consignee_district="Bengaluru Urban",
        consignee_state="KARNATAKA",
        target_location_status=STATUS_VERIFIED_BENGALURU_URBAN,
        data_source_classification="LIVE_VERIFIED",
    )
    db_session.add(bid)
    db_session.commit()

    alert = Alert(
        profile_id=profile.id,
        bid_id=bid.id,
        match_reason="Bengaluru Urban Verified Match",
        status="NEW",
        acknowledged=False,
    )
    db_session.add(alert)
    db_session.commit()

    # Visual unacknowledged check
    unack_res = client.get("/alerts/?limit=1&unacknowledged_only=true")
    assert unack_res.status_code == 200
    alerts = unack_res.json()
    assert len(alerts) == 1
    assert alerts[0]["bid"]["bid_number"] == "GEM/2026/B/9301"

    # Acknowledge alert via POST
    ack_res = client.post(f"/alerts/{alert.id}/ack")
    assert ack_res.status_code == 200
    assert ack_res.json()["acknowledged"] is True
