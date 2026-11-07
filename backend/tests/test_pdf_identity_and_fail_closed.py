"""
Authoritative Test Suite for GeM Bid-to-PDF Identity Verification & Fail-Closed Scenarios
Tests Scenarios A through J:
  Scenario A: Correct bid ID + Bengaluru delivery -> VERIFIED
  Scenario B: Correct bid ID + Gujarat delivery -> LOCATION_MISMATCH
  Scenario C: Different bid ID inside PDF -> PDF_BID_MISMATCH
  Scenario D: PDF from 2025 attached to 2026 bid -> DOCUMENT_VERSION_MISMATCH
  Scenario E: Checksum validation and cache invalidation
  Scenario F: Gujarat address in PDF with Bengaluru fallback in DB -> REJECT (never VERIFIED)
  Scenario G: Missing bid ID in PDF -> OCR_UNCERTAIN / REVIEW (never VERIFIED)
  Scenario H: Multiple corrigenda -> latest valid official deadline used
  Scenario I: PDF extraction failure / 0 bytes -> SOURCE_UNAVAILABLE
  Scenario J: Conflicting dates aligned to official PDF evidence
"""
import os
import io
import pytest
from datetime import datetime, timezone, timedelta

from app.models.bid import Bid
from app.models.alert import Alert
from app.models.profile import Profile
from app.services.pdf_synchronizer import (
    synchronize_bid_with_pdf,
    STATUS_VERIFIED,
    STATUS_PDF_BID_MISMATCH,
    STATUS_LOCATION_MISMATCH,
    STATUS_DOCUMENT_VERSION_MISMATCH,
    STATUS_OCR_UNCERTAIN,
    STATUS_SOURCE_UNAVAILABLE,
)
from app.services.location_normalizer import (
    STATUS_VERIFIED_BENGALURU_URBAN,
    STATUS_VERIFIED_BENGALURU_CITY,
    STATUS_OUTSIDE_TARGET,
    STATUS_AMBIGUOUS,
    STATUS_UNKNOWN,
)

# Real PDF asset paths
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

BANGALORE_CANDIDATES = [
    os.path.join(ROOT_DIR, "test_gem_9993172.pdf"),
    os.path.abspath(os.path.join(ROOT_DIR, "..", "test_gem_9993172.pdf")),
]
PDF_BANGALORE_PATH = next((p for p in BANGALORE_CANDIDATES if os.path.exists(p)), BANGALORE_CANDIDATES[0])

GUJARAT_CANDIDATES = [
    os.path.join(ROOT_DIR, "test_gem_8219903_gujarat.pdf"),
    os.path.join(ROOT_DIR, "debug_bid_8219903.pdf"),
    os.path.abspath(os.path.join(ROOT_DIR, "..", "debug_bid_8219903.pdf")),
]
PDF_GUJARAT_PATH = next((p for p in GUJARAT_CANDIDATES if os.path.exists(p)), GUJARAT_CANDIDATES[0])


def build_synthetic_pdf(bid_number: str, dated: str, consignee_lines: list) -> bytes:
    """Generate a valid minimal PDF with specific text contents for testing."""
    lines = [
        f"Bid Number: {bid_number}",
        f"Dated: {dated}",
        "Bid End Date/Time: 28-11-2026 15:00:00",
        "Item Category: Computer Printer (V2)",
        "Ministry/State Name: Ministry of Science and Technology",
        "Department Name: Department of Space",
        "Consignee/Reporting Officer and Quantity:",
    ] + consignee_lines
    stream_content = "BT /F1 10 Tf 50 750 Td " + " T* ".join(f"({l}) Tj" for l in lines) + " ET"
    pdf = f"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length {len(stream_content)} >> stream
{stream_content}
endstream
endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000340 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
450
%%EOF"""
    return pdf.encode("latin-1")


# ─── SCENARIO A: Correct Bid ID + Bengaluru Delivery -> VERIFIED ───────────────
def test_scenario_a_correct_bid_and_bengaluru_delivery(db_session):
    """Scenario A: Official ISRO PDF matches bid number and Bangalore Urban address -> VERIFIED."""
    assert os.path.exists(PDF_BANGALORE_PATH), "Official Bangalore test PDF must exist"
    with open(PDF_BANGALORE_PATH, "rb") as f:
        pdf_bytes = f.read()

    bid = Bid(
        gem_bid_id=8123875,
        bid_number="GEM/2026/B/8123875",
        category_name="Computer Printer (V2)",
        dept_name="ISRO Headquarters Bangalore",
        start_date=datetime(2026, 10, 16, tzinfo=timezone.utc),
        end_date=datetime(2026, 11, 28, tzinfo=timezone.utc),
        status=1,
    )
    db_session.add(bid)
    db_session.commit()

    res = synchronize_bid_with_pdf(bid, pdf_bytes=pdf_bytes, db=db_session)

    assert res.is_bid_matched is True
    assert res.synchronization_status == STATUS_VERIFIED
    assert res.target_location_status == STATUS_VERIFIED_BENGALURU_URBAN
    assert "VERIFIED" in res.verification_reason
    assert bid.synchronization_status == STATUS_VERIFIED
    assert bid.target_location_status == STATUS_VERIFIED_BENGALURU_URBAN


# ─── SCENARIO B: Correct Bid ID + Gujarat Delivery -> LOCATION_MISMATCH ────────
def test_scenario_b_correct_bid_and_gujarat_delivery(db_session):
    """Scenario B: Bid number matches, but PDF delivery address is in Gujarat -> LOCATION_MISMATCH."""
    assert os.path.exists(PDF_GUJARAT_PATH), "Gujarat test PDF must exist"
    with open(PDF_GUJARAT_PATH, "rb") as f:
        pdf_bytes = f.read()

    # The PDF contains bid number GEM/2025/B/6568333 with Nadiad, Gujarat
    bid = Bid(
        gem_bid_id=6568333,
        bid_number="GEM/2025/B/6568333",
        category_name="Battery Link Terminal",
        dept_name="Gujarat State Road Transport",
        start_date=datetime(2025, 8, 13, tzinfo=timezone.utc),
        end_date=datetime(2026, 11, 28, tzinfo=timezone.utc),
        status=1,
    )
    db_session.add(bid)
    db_session.commit()

    res = synchronize_bid_with_pdf(bid, pdf_bytes=pdf_bytes, db=db_session)

    assert res.is_bid_matched is True
    assert res.synchronization_status == STATUS_LOCATION_MISMATCH
    assert res.target_location_status == STATUS_OUTSIDE_TARGET
    assert "LOCATION_MISMATCH" in res.verification_reason
    assert "GUJARAT" in (res.extracted_state or "").upper()
    assert bid.synchronization_status == STATUS_LOCATION_MISMATCH
    assert bid.target_location_status == STATUS_OUTSIDE_TARGET


# ─── SCENARIO C: Different Bid ID inside PDF -> PDF_BID_MISMATCH ───────────────
def test_scenario_c_different_bid_id_inside_pdf(db_session):
    """Scenario C: Registered 2026 bid linked to PDF with different bid ID -> PDF_BID_MISMATCH."""
    pdf_bytes = build_synthetic_pdf(
        bid_number="GEM/2026/B/7777777",
        dated="10-11-2026",
        consignee_lines=["Bangalore Urban, Karnataka, 560001"]
    )

    bid = Bid(
        gem_bid_id=8219903,
        bid_number="GEM/2026/B/8219903",
        category_name="Toner Cartridges",
        status=1,
    )
    db_session.add(bid)
    db_session.commit()

    res = synchronize_bid_with_pdf(bid, pdf_bytes=pdf_bytes, db=db_session)

    assert res.is_bid_matched is False
    assert res.synchronization_status == STATUS_PDF_BID_MISMATCH
    assert res.target_location_status == STATUS_AMBIGUOUS
    assert "PDF_BID_MISMATCH" in res.verification_reason
    assert "GEM/2026/B/7777777" in res.verification_reason
    assert bid.synchronization_status == STATUS_PDF_BID_MISMATCH
    assert bid.target_location_status == STATUS_AMBIGUOUS


# ─── SCENARIO D: PDF from 2025 attached to 2026 bid -> DOCUMENT_VERSION_MISMATCH
def test_scenario_d_year_mismatch_2025_pdf_on_2026_bid(db_session):
    """Scenario D: 2025 PDF attached to 2026 bid (reproduced live bug) -> DOCUMENT_VERSION_MISMATCH."""
    assert os.path.exists(PDF_GUJARAT_PATH)
    with open(PDF_GUJARAT_PATH, "rb") as f:
        pdf_bytes = f.read()

    # The PDF contains GEM/2025/B/6568333
    bid = Bid(
        gem_bid_id=8219903,
        bid_number="GEM/2026/B/8219903",
        category_name="Toner Cartridges",
        status=1,
    )
    db_session.add(bid)
    db_session.commit()

    res = synchronize_bid_with_pdf(bid, pdf_bytes=pdf_bytes, db=db_session)

    assert res.is_bid_matched is False
    assert res.synchronization_status == STATUS_DOCUMENT_VERSION_MISMATCH
    assert res.target_location_status == STATUS_AMBIGUOUS
    assert "DOCUMENT_VERSION_MISMATCH" in res.verification_reason
    assert bid.synchronization_status == STATUS_DOCUMENT_VERSION_MISMATCH
    assert bid.target_location_status == STATUS_AMBIGUOUS


# ─── SCENARIO E: Checksum Cache & Invalidation ────────────────────────────────
def test_scenario_e_checksum_cache_and_invalidation(db_session):
    """Scenario E: If document checksum matches and is verified, cached result is accepted; force invalidates."""
    assert os.path.exists(PDF_BANGALORE_PATH)
    with open(PDF_BANGALORE_PATH, "rb") as f:
        pdf_bytes = f.read()

    bid = Bid(
        gem_bid_id=8123875,
        bid_number="GEM/2026/B/8123875",
        status=1,
    )
    db_session.add(bid)
    db_session.commit()

    res1 = synchronize_bid_with_pdf(bid, pdf_bytes=pdf_bytes, db=db_session)
    assert res1.synchronization_status == STATUS_VERIFIED

    # Second run without force should hit cache
    res2 = synchronize_bid_with_pdf(bid, pdf_bytes=pdf_bytes, force=False, db=db_session)
    assert res2.synchronization_status == STATUS_VERIFIED
    assert res2.original_pdf_checksum == res1.original_pdf_checksum

    # Force re-synchronization
    res3 = synchronize_bid_with_pdf(bid, pdf_bytes=pdf_bytes, force=True, db=db_session)
    assert res3.synchronization_status == STATUS_VERIFIED


# ─── SCENARIO F: Gujarat Address in PDF with Bengaluru Fallback in DB ──────────
def test_scenario_f_gujarat_address_with_bengaluru_db_fallback(db_session):
    """
    Scenario F: Database record has buyer_city='Bangalore' and dept_name='IISc Bangalore',
    but actual PDF evidence contains a Gujarat address.
    PDF evidence MUST override DB text. Status must be LOCATION_MISMATCH, NEVER VERIFIED.
    """
    pdf_bytes = build_synthetic_pdf(
        bid_number="GEM/2026/B/5555555",
        dated="15-10-2026",
        consignee_lines=[
            "Consignee: Patel Rameshbhai",
            "Address: GIDC Industrial Estate, Nadiad, Kheda, Gujarat - 387001"
        ]
    )

    bid = Bid(
        gem_bid_id=5555555,
        bid_number="GEM/2026/B/5555555",
        buyer_city="Bangalore",
        buyer_state="KARNATAKA",
        dept_name="Indian Institute of Science Bangalore",
        status=1,
    )
    db_session.add(bid)
    db_session.commit()

    res = synchronize_bid_with_pdf(bid, pdf_bytes=pdf_bytes, db=db_session)

    assert res.synchronization_status == STATUS_LOCATION_MISMATCH
    assert res.target_location_status == STATUS_OUTSIDE_TARGET
    assert "LOCATION_MISMATCH" in res.verification_reason
    assert bid.target_location_status == STATUS_OUTSIDE_TARGET


# ─── SCENARIO G: Missing Bid ID in PDF -> OCR_UNCERTAIN / AMBIGUOUS ────────────
def test_scenario_g_missing_bid_id_in_pdf(db_session):
    """Scenario G: PDF without identifiable Bid Number is OCR_UNCERTAIN, never VERIFIED."""
    # Synthetic PDF with no Bid Number pattern
    stream_content = "BT /F1 10 Tf 50 750 Td (Generic Document Without Bid ID) Tj ET"
    empty_pdf = f"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length {len(stream_content)} >> stream
{stream_content}
endstream
endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000340 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
450
%%EOF""".encode("latin-1")

    bid = Bid(
        gem_bid_id=4444444,
        bid_number="GEM/2026/B/4444444",
        status=1,
    )
    db_session.add(bid)
    db_session.commit()

    res = synchronize_bid_with_pdf(bid, pdf_bytes=empty_pdf, db=db_session)

    assert res.is_bid_matched is False
    assert res.synchronization_status == STATUS_OCR_UNCERTAIN
    assert res.target_location_status == STATUS_AMBIGUOUS
    assert bid.synchronization_status == STATUS_OCR_UNCERTAIN


# ─── SCENARIO H: Corrigendum Extension Keeps Bid Active ───────────────────────
def test_scenario_h_corrigendum_extension(db_session):
    """Scenario H: When corrigendum extends deadline, revised deadline is used."""
    pdf_bytes = build_synthetic_pdf(
        bid_number="GEM/2026/B/3333333",
        dated="01-10-2026",
        consignee_lines=["Bangalore Urban, Karnataka - 560094"]
    )

    now = datetime.now(timezone.utc)
    bid = Bid(
        gem_bid_id=3333333,
        bid_number="GEM/2026/B/3333333",
        original_end_date=now - timedelta(days=2),  # Past original deadline
        revised_end_date=now + timedelta(days=5),   # Extended via corrigendum
        corrigendum_status="EXTENDED",
        corrigendum_details="Deadline extended by Corrigendum 1",
        status=1,
    )
    db_session.add(bid)
    db_session.commit()

    res = synchronize_bid_with_pdf(bid, pdf_bytes=pdf_bytes, db=db_session)

    assert res.synchronization_status == STATUS_VERIFIED
    assert res.latest_verified_status == "ACTIVE"
    assert res.corrigendum_status == "EXTENDED"


# ─── SCENARIO I: Extraction Failure / 0 Bytes -> SOURCE_UNAVAILABLE ────────────
def test_scenario_i_extraction_failure_empty_pdf(db_session):
    """Scenario I: 0 bytes or unreachable source results in SOURCE_UNAVAILABLE, routed to Review Queue."""
    bid = Bid(
        gem_bid_id=2222222,
        bid_number="GEM/2026/B/2222222",
        status=1,
    )
    db_session.add(bid)
    db_session.commit()

    res = synchronize_bid_with_pdf(bid, pdf_bytes=b"", db=db_session)

    assert res.synchronization_status == STATUS_SOURCE_UNAVAILABLE
    assert res.target_location_status == STATUS_UNKNOWN
    assert "SOURCE_UNAVAILABLE" in res.verification_reason
    assert bid.synchronization_status == STATUS_SOURCE_UNAVAILABLE
    assert bid.target_location_status == STATUS_UNKNOWN


# ─── SCENARIO J: Date Synchronization from PDF ────────────────────────────────
def test_scenario_j_date_synchronization_from_pdf(db_session):
    """Scenario J: Publication date and deadline are extracted from official PDF header."""
    pdf_bytes = build_synthetic_pdf(
        bid_number="GEM/2026/B/1111111",
        dated="12-10-2026",
        consignee_lines=["Bangalore Urban, Karnataka - 560001"]
    )

    bid = Bid(
        gem_bid_id=1111111,
        bid_number="GEM/2026/B/1111111",
        start_date=None,  # Missing start date in DB
        status=1,
    )
    db_session.add(bid)
    db_session.commit()

    res = synchronize_bid_with_pdf(bid, pdf_bytes=pdf_bytes, db=db_session)

    assert res.synchronization_status == STATUS_VERIFIED
    assert res.original_publication_date is not None
    from app.services.datetime_service import to_ist
    ist_pub = to_ist(res.original_publication_date)
    assert ist_pub.year == 2026
    assert ist_pub.month == 10
    assert ist_pub.day == 12


# ─── API LEVEL FAIL-CLOSED ROUTING TESTS ──────────────────────────────────────
def test_api_quarantined_bid_excluded_from_verified_feed(client, db_session):
    """Verify that GEM/2026/B/8219903 never appears in /bids/?scope=verified."""
    # Seed 1 verified and 1 quarantined bid
    b_verified = Bid(
        gem_bid_id=8123875,
        bid_number="GEM/2026/B/8123875",
        target_location_status="VERIFIED_BENGALURU_URBAN",
        synchronization_status="VERIFIED",
        pdf_verification_status="VERIFIED",
        end_date=datetime.now(timezone.utc) + timedelta(days=10),
        status=1,
    )
    b_quarantined = Bid(
        gem_bid_id=8219903,
        bid_number="GEM/2026/B/8219903",
        target_location_status="AMBIGUOUS",
        synchronization_status="PDF_BID_MISMATCH",
        pdf_verification_status="PDF_BID_MISMATCH",
        verification_reason="PDF_BID_MISMATCH: Contains GEM/2025/B/6568333 in Gujarat",
        end_date=datetime.now(timezone.utc) + timedelta(days=10),
        status=1,
    )
    db_session.add_all([b_verified, b_quarantined])
    db_session.commit()

    # Query Verified Feed
    res_verified = client.get("/bids/?scope=verified")
    assert res_verified.status_code == 200
    data_v = res_verified.json()
    b_ids_v = [b["bid_number"] for b in data_v]
    assert "GEM/2026/B/8123875" in b_ids_v
    assert "GEM/2026/B/8219903" not in b_ids_v

    # Query Review Queue
    res_review = client.get("/bids/?scope=review")
    assert res_review.status_code == 200
    data_r = res_review.json()
    b_ids_r = [b["bid_number"] for b in data_r]
    assert "GEM/2026/B/8219903" in b_ids_r
    quarantined_record = next(b for b in data_r if b["bid_number"] == "GEM/2026/B/8219903")
    assert quarantined_record["synchronization_status"] == "PDF_BID_MISMATCH"
    assert "PDF_BID_MISMATCH" in quarantined_record["verification_reason"]


def test_api_summary_stats_strict_fail_closed_counts(client, db_session):
    """Verify that /bids/summary/stats counts only genuinely verified bids."""
    b_verified = Bid(
        gem_bid_id=8123875,
        bid_number="GEM/2026/B/8123875",
        target_location_status="VERIFIED_BENGALURU_URBAN",
        synchronization_status="VERIFIED",
        pdf_verification_status="VERIFIED",
        end_date=datetime.now(timezone.utc) + timedelta(days=10),
        status=1,
    )
    b_mismatch = Bid(
        gem_bid_id=8219903,
        bid_number="GEM/2026/B/8219903",
        target_location_status="AMBIGUOUS",
        synchronization_status="PDF_BID_MISMATCH",
        pdf_verification_status="PDF_BID_MISMATCH",
        end_date=datetime.now(timezone.utc) + timedelta(days=10),
        status=1,
    )
    db_session.add_all([b_verified, b_mismatch])
    db_session.commit()

    res = client.get("/bids/summary/stats")
    assert res.status_code == 200
    stats = res.json()
    assert stats["bengaluru_urban_verified"] == 1
    assert stats["bengaluru_total_verified"] == 1
    assert stats["review_count"] == 1
