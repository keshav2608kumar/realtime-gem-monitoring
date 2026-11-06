"""
GeM BidWatch — Tests
Covers: API endpoints, filter matcher, bid normalizer, real GeM integration.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Use in-memory SQLite with StaticPool so all connections share the same database
TEST_DB_URL = "sqlite:///:memory:"

# Override settings before importing app
import os
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["MONITOR_ENABLED"] = "false"  # Don't start scheduler in tests

from app.database import Base, get_db
from app.main import app

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test, drop after."""
    # Import all models to ensure they are registered with Base
    from app.models.bid import Bid          # noqa
    from app.models.profile import Profile  # noqa
    from app.models.alert import Alert      # noqa
    from app.models.device import Device    # noqa
    from app.models.health import MonitorHealth  # noqa
    # Also import database Base
    from app.database import Base as AppBase
    AppBase.metadata.create_all(bind=engine)
    yield
    AppBase.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ─── ROOT ─────────────────────────────────────────────────────────────────────

def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["app"] == "GeM BidWatch"


# ─── PROFILES ─────────────────────────────────────────────────────────────────

def test_create_profile(client):
    payload = {
        "name": "Bangalore Toner",
        "state": "KARNATAKA",
        "cities": ["BANGALORE", "Bangalore Urban", "BENGALURU URBAN", "Bengaluru"],
        "keywords": ["toner", "cartridge", "printer", "ink"],
        "is_active": True,
        "poll_interval_seconds": 300,
    }
    r = client.post("/profiles/", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Bangalore Toner"
    assert data["state"] == "KARNATAKA"
    assert "toner" in data["keywords"]
    assert data["id"] is not None


def test_list_profiles(client):
    client.post("/profiles/", json={"name": "P1", "state": "KARNATAKA", "keywords": ["printer"]})
    client.post("/profiles/", json={"name": "P2", "state": "KARNATAKA", "keywords": ["toner"]})
    r = client.get("/profiles/")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_update_profile(client):
    r = client.post("/profiles/", json={"name": "P1", "state": "KARNATAKA"})
    pid = r.json()["id"]
    r2 = client.patch(f"/profiles/{pid}", json={"name": "Updated"})
    assert r2.status_code == 200
    assert r2.json()["name"] == "Updated"


def test_delete_profile(client):
    r = client.post("/profiles/", json={"name": "P1", "state": "KARNATAKA"})
    pid = r.json()["id"]
    r2 = client.delete(f"/profiles/{pid}")
    assert r2.status_code == 204
    r3 = client.get(f"/profiles/{pid}")
    assert r3.status_code == 404


# ─── BIDS ─────────────────────────────────────────────────────────────────────

def test_list_bids_empty(client):
    r = client.get("/bids/")
    assert r.status_code == 200
    assert r.json() == []


def test_batch_sync_bids(client):
    # 1. Create a profile
    client.post("/profiles/", json={
        "name": "Bangalore Toner",
        "state": "KARNATAKA",
        "cities": ["BANGALORE", "Bangalore Urban"],
        "keywords": ["toner", "printer"],
        "is_active": True,
    })

    # 2. Batch sync 2 bids (one matching, one not)
    payload = [
        {
            "gem_bid_id": 111,
            "bid_number": "GEM/2026/B/111",
            "category_name": "HP Laserjet Toner Cartridge",
            "consignee_state": "KARNATAKA",
            "consignee_city": "BANGALORE",
            "bid_url": "https://bidplus.gem.gov.in/showbidDocument/111",
        },
        {
            "gem_bid_id": 222,
            "bid_number": "GEM/2026/B/222",
            "category_name": "Cleaning Broom Mop",
            "consignee_state": "KARNATAKA",
            "consignee_city": "BANGALORE",
            "bid_url": "https://bidplus.gem.gov.in/showbidDocument/222",
        }
    ]
    r = client.post("/bids/batch-sync", json=payload)
    assert r.status_code == 201
    res = r.json()
    assert res["bids_received"] == 2
    assert res["bids_inserted"] == 2
    assert res["alerts_created"] == 1

    # 3. Check /bids/ list
    bids_res = client.get("/bids/")
    assert len(bids_res.json()) == 2

    # 4. Check /alerts/ list
    alerts_res = client.get("/alerts/")
    assert len(alerts_res.json()) == 1
    assert alerts_res.json()[0]["bid"]["bid_number"] == "GEM/2026/B/111"


def test_devices(client):
    r = client.post("/devices/", json={"fcm_token": "test-token-abc123456789", "device_name": "My Phone"})
    assert r.status_code == 201
    # Register same token again — should update not duplicate
    r2 = client.post("/devices/", json={"fcm_token": "test-token-abc123456789", "device_name": "My Phone v2"})
    assert r2.status_code == 201
    r3 = client.get("/devices/")
    assert len(r3.json()) == 1  # Still only one device


# ─── HEALTH ───────────────────────────────────────────────────────────────────

def test_health_status(client):
    r = client.get("/health/")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["total_profiles"] == 0
    assert data["total_bids_in_db"] == 0


# ─── FILTER MATCHER ───────────────────────────────────────────────────────────

def test_filter_matcher_keyword_match():
    from app.gem.filter_matcher import match_bid_to_profile
    from app.schemas import BidCreate, ProfileOut
    from datetime import datetime, timezone

    bid = BidCreate(
        gem_bid_id=12345,
        bid_number="GEM/2026/B/999",
        category_name="HP LaserJet Toner Cartridge Black",
        consignee_state="KARNATAKA",
        consignee_city="BANGALORE",
    )
    profile = ProfileOut(
        id=1,
        name="Test",
        state="KARNATAKA",
        keywords=["toner", "cartridge", "printer"],
        is_active=True,
        poll_interval_seconds=300,
        created_at=datetime.now(timezone.utc),
    )
    result = match_bid_to_profile(bid, profile)
    assert result.matched is True
    assert "toner" in result.matched_keywords
    assert "cartridge" in result.matched_keywords


def test_filter_matcher_no_match():
    from app.gem.filter_matcher import match_bid_to_profile
    from app.schemas import BidCreate, ProfileOut
    from datetime import datetime, timezone

    bid = BidCreate(
        gem_bid_id=99999,
        bid_number="GEM/2026/B/000",
        category_name="Office Chairs Ergonomic",
        consignee_state="KARNATAKA",
        consignee_city="BANGALORE",
    )
    profile = ProfileOut(
        id=1,
        name="Test",
        state="KARNATAKA",
        keywords=["toner", "cartridge", "printer"],
        is_active=True,
        poll_interval_seconds=300,
        created_at=datetime.now(timezone.utc),
    )
    result = match_bid_to_profile(bid, profile)
    assert result.matched is False


def test_filter_matcher_no_keyword_filter():
    """When profile has no keywords, ALL bids match."""
    from app.gem.filter_matcher import match_bid_to_profile
    from app.schemas import BidCreate, ProfileOut
    from datetime import datetime, timezone

    bid = BidCreate(
        gem_bid_id=11111,
        bid_number="GEM/2026/B/111",
        category_name="Anything at all",
        consignee_state="KARNATAKA",
    )
    profile = ProfileOut(
        id=1,
        name="All Bids",
        state="KARNATAKA",
        keywords=None,
        is_active=True,
        poll_interval_seconds=300,
        created_at=datetime.now(timezone.utc),
    )
    result = match_bid_to_profile(bid, profile)
    assert result.matched is True


# ─── BID NORMALIZER ───────────────────────────────────────────────────────────

def test_normalizer_basic():
    from app.gem.fetcher import RawBid
    from app.gem.normalizer import normalize_bid

    raw_data = {
        "b_id": [10049786],
        "b_bid_number": ["GEM/2026/B/8173777"],
        "b_category_name": ["Toner Cartridge Genuine HP"],
        "b_total_quantity": [50],
        "b_bid_type": [1],
        "b_status": [1],
        "is_high_value": [False],
        "ba_official_details_minName": ["Ministry of Railways"],
        "ba_official_details_deptName": ["Indian Railways"],
        "final_start_date_sort": ["2026-10-16T19:59:53Z"],
        "final_end_date_sort": ["2026-11-20T20:00:00Z"],
        "b_cat_id": ["home_univ_univ_univ_univ"],
    }
    raw = RawBid(raw_data, "KARNATAKA", "BANGALORE")
    result = normalize_bid(raw)

    assert result is not None
    assert result.gem_bid_id == 10049786
    assert result.bid_number == "GEM/2026/B/8173777"
    assert result.category_name == "Toner Cartridge Genuine HP"
    assert result.quantity == 50
    assert result.consignee_state == "KARNATAKA"
    assert result.consignee_city == "BANGALORE"
    assert result.bid_url.startswith("https://bidplus.gem.gov.in/showbidDocument/")
    assert result.start_date is not None
    assert result.end_date is not None


def test_normalizer_missing_id_returns_none():
    from app.gem.fetcher import RawBid
    from app.gem.normalizer import normalize_bid

    raw = RawBid({"b_category_name": ["Something"]}, "KARNATAKA", "BANGALORE")
    result = normalize_bid(raw)
    assert result is None
