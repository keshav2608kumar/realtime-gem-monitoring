"""
GeM BidWatch — Authoritative PDF & Bid Synchronization Engine
Implements strict fail-closed document-to-bid identity verification:

Statuses:
- VERIFIED: Exact bid ID, current version, verified Bengaluru delivery, and valid dates.
- PDF_BID_MISMATCH: PDF belongs to another tender or contains a different bid ID.
- LOCATION_MISMATCH: PDF delivery address is outside Bengaluru Urban / City (e.g. Gujarat, Dehradun).
- DATE_MISMATCH: Conflicting dates without valid corrigendum.
- DOCUMENT_VERSION_MISMATCH: Outdated document or year mismatch (e.g. 2025 PDF for 2026 bid).
- OCR_UNCERTAIN: Scanned document, unindexed text, or ambiguous address.
- SOURCE_UNAVAILABLE: PDF document missing, 0 bytes, or unreachable from source.
- UNKNOWN: Insufficient evidence.

NON-NEGOTIABLE RULE: If the application cannot prove that a PDF belongs to the exact bid
and that the delivery address belongs to that same PDF, the bid must NOT be marked VERIFIED.
"""

import io
import re
import hashlib
import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.models.bid import Bid
from app.services.location_normalizer import (
    resolve_effective_bid_delivery_location,
    STATUS_VERIFIED_BENGALURU_URBAN,
    STATUS_VERIFIED_BENGALURU_RURAL,
    STATUS_VERIFIED_BENGALURU_CITY,
    STATUS_PARTIALLY_VERIFIED,
    STATUS_AMBIGUOUS,
    STATUS_OUTSIDE_TARGET,
    STATUS_UNKNOWN,
)
from app.services.pdf_location_extractor import (
    extract_location_from_pdf,
    fetch_pdf_bytes,
    compute_doc_hash,
    ExtractedDeliveryLocation,
)
from app.services.bid_status_service import (
    calculate_bid_status,
    STATUS_ACTIVE,
    STATUS_CLOSING_SOON,
    STATUS_EXPIRED,
    STATUS_CANCELLED,
)

logger = logging.getLogger(__name__)

# Mandatory Fail-Closed Verification Statuses
STATUS_VERIFIED = "VERIFIED"
STATUS_PDF_BID_MISMATCH = "PDF_BID_MISMATCH"
STATUS_LOCATION_MISMATCH = "LOCATION_MISMATCH"
STATUS_DATE_MISMATCH = "DATE_MISMATCH"
STATUS_DOCUMENT_VERSION_MISMATCH = "DOCUMENT_VERSION_MISMATCH"
STATUS_OCR_UNCERTAIN = "OCR_UNCERTAIN"
STATUS_SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
STATUS_UNKNOWN_SYNC = "UNKNOWN"

# Backward-compatibility alias
SYNC_SYNCHRONIZED = STATUS_VERIFIED
SYNC_DATA_MISMATCH = STATUS_PDF_BID_MISMATCH
SYNC_FAILED = STATUS_OCR_UNCERTAIN
SYNC_PDF_UNAVAILABLE = STATUS_SOURCE_UNAVAILABLE
SYNC_PENDING = "PENDING"


@dataclass
class PdfSyncResult:
    bid_id: Optional[int] = None
    bid_number: Optional[str] = None
    pdf_bid_number: Optional[str] = None
    is_bid_matched: bool = False
    official_source_url: Optional[str] = None
    original_pdf_url: Optional[str] = None
    original_pdf_checksum: Optional[str] = None
    document_version: str = "1.0"
    original_publication_date: Optional[datetime] = None
    original_deadline: Optional[datetime] = None
    latest_revised_deadline: Optional[datetime] = None
    corrigendum_reference: Optional[str] = None
    corrigendum_date: Optional[datetime] = None
    corrigendum_status: str = "NONE"
    latest_verified_status: str = "UNKNOWN"
    raw_extracted_text: Optional[str] = None
    extracted_category: Optional[str] = None
    extracted_consignee_name: Optional[str] = None
    extracted_delivery_address: Optional[str] = None
    extracted_city: Optional[str] = None
    extracted_district: Optional[str] = None
    extracted_state: Optional[str] = None
    extracted_pincode: Optional[str] = None
    pdf_details_page_number: Optional[int] = None
    pdf_consignee_page_number: Optional[int] = None
    extraction_timestamp: Optional[datetime] = None
    verification_timestamp: Optional[datetime] = None
    data_confidence: float = 0.0
    synchronization_status: str = STATUS_UNKNOWN_SYNC
    target_location_status: str = STATUS_UNKNOWN
    verification_reason: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def parse_gem_ist_datetime(date_str: str) -> Optional[datetime]:
    """Parse GeM date/time strings into an aware UTC datetime object."""
    if not date_str:
        return None
    cleaned = date_str.strip()
    ist_tz = timezone(timedelta(hours=5, minutes=30))

    formats = [
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d-%m-%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(cleaned, fmt)
            dt_ist = dt.replace(tzinfo=ist_tz)
            return dt_ist.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def extract_metadata_from_page_1(page_text: str) -> Dict[str, Any]:
    """Extract authoritative header fields from Page 1 of GeM bid document."""
    result: Dict[str, Any] = {
        "pdf_bid_number": None,
        "dated_str": None,
        "end_date_str": None,
        "opening_date_str": None,
        "category_str": None,
        "ministry_str": None,
        "dept_str": None,
        "org_str": None,
    }
    if not page_text:
        return result

    # 1. Bid Number: 'Bid Number: GEM/2026/B/8123875' or 'Bid Number / GEM/...'
    bid_m = re.search(r"Bid\s*Number\s*[:/]?\s*(GEM/\d{4}/[A-Z]/\d+)", page_text, re.IGNORECASE)
    if not bid_m:
        bid_m = re.search(r"\b(GEM/\d{4}/[A-Z]/\d+)\b", page_text)
    if bid_m:
        result["pdf_bid_number"] = bid_m.group(1).strip()

    # 2. Dated: 'Dated: 16-10-2026' or 'Dated / 16-10-2026'
    dated_m = re.search(r"Dated\s*[:/]?\s*(\d{2}-\d{2}-\d{4})", page_text, re.IGNORECASE)
    if dated_m:
        result["dated_str"] = dated_m.group(1).strip()

    # 3. Bid End Date/Time: 'Bid End Date/Time 28-10-2026 13:00:00'
    end_m = re.search(r"Bid\s*End\s*Date/Time\s*[:/]?\s*(\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2})", page_text, re.IGNORECASE)
    if not end_m:
        end_m = re.search(r"Bid\s*End\s*Date/Time\s*[:/]?\s*(\d{2}-\d{2}-\d{4})", page_text, re.IGNORECASE)
    if end_m:
        result["end_date_str"] = end_m.group(1).strip()

    # 4. Item Category: 'Item Category Computer Printer (V2) (Q2)'
    cat_m = re.search(r"Item\s*Category\s*[:/]?\s*([^\n\r]+)", page_text, re.IGNORECASE)
    if cat_m:
        cat_candidate = cat_m.group(1).strip()
        clean_cat = re.sub(r"\s*\(Q\d+\)\s*$", "", cat_candidate)
        result["category_str"] = clean_cat.strip()

    # 5. Ministry & Department
    min_m = re.search(r"Ministry/State\s*Name\s*[:/]?\s*([^\n\r]+)", page_text, re.IGNORECASE)
    if min_m:
        result["ministry_str"] = min_m.group(1).strip()

    dept_m = re.search(r"Department\s*Name\s*[:/]?\s*([^\n\r]+)", page_text, re.IGNORECASE)
    if dept_m:
        result["dept_str"] = dept_m.group(1).strip()

    org_m = re.search(r"Organisation\s*Name\s*[:/]?\s*([^\n\r]+)", page_text, re.IGNORECASE)
    if org_m:
        result["org_str"] = org_m.group(1).strip()

    return result


def synchronize_bid_with_pdf(
    bid: Bid,
    pdf_bytes: Optional[bytes] = None,
    pdf_path: Optional[str] = None,
    pdf_url: Optional[str] = None,
    force: bool = False,
    db: Optional[Session] = None,
) -> PdfSyncResult:
    """
    Execute full authoritative fail-closed synchronization between Bid record and PDF document.
    """
    now_utc = datetime.now(timezone.utc)
    target_url = pdf_url or bid.bid_url or bid.original_pdf_url

    # Check for available document sources
    raw_content: Optional[bytes] = None
    if pdf_bytes:
        raw_content = pdf_bytes
    elif pdf_path:
        try:
            with open(pdf_path, "rb") as f:
                raw_content = f.read()
        except Exception as e:
            logger.warning(f"Could not read local PDF {pdf_path}: {e}")
    elif target_url:
        raw_content = fetch_pdf_bytes(target_url)

    # 1. Fail-Closed Check: Missing or Empty Document
    if not raw_content or len(raw_content) < 50:
        reason = "SOURCE_UNAVAILABLE: Official PDF document could not be retrieved from GeM portal."
        res = PdfSyncResult(
            bid_id=bid.id,
            bid_number=bid.bid_number,
            official_source_url=target_url,
            original_pdf_url=target_url,
            synchronization_status=STATUS_SOURCE_UNAVAILABLE,
            latest_verified_status="UNKNOWN",
            target_location_status=STATUS_UNKNOWN,  # Route to Review Queue
            extraction_timestamp=now_utc,
            verification_timestamp=now_utc,
            verification_reason=reason,
            error_message=reason,
        )
        if db:
            bid.synchronization_status = STATUS_SOURCE_UNAVAILABLE
            bid.pdf_verification_status = "PDF_UNAVAILABLE"
            bid.target_location_status = STATUS_UNKNOWN
            bid.verification_reason = reason
            bid.verification_timestamp = now_utc
            try:
                db.commit()
            except Exception:
                db.rollback()
        return res

    doc_checksum = compute_doc_hash(raw_content)

    # 2. Checksum Cache (Skip re-processing if unchanged unless force=True)
    if (
        not force
        and bid.original_pdf_checksum == doc_checksum
        and bid.synchronization_status in (STATUS_VERIFIED, SYNC_SYNCHRONIZED)
        and bid.target_location_status in (STATUS_VERIFIED_BENGALURU_URBAN, STATUS_VERIFIED_BENGALURU_RURAL, STATUS_VERIFIED_BENGALURU_CITY)
    ):
        logger.info(f"Bid {bid.bid_number} PDF checksum unchanged ({doc_checksum[:8]}); cached verified.")
        return PdfSyncResult(
            bid_id=bid.id,
            bid_number=bid.bid_number,
            pdf_bid_number=bid.pdf_bid_number or bid.bid_number,
            is_bid_matched=True,
            official_source_url=bid.official_source_url or target_url,
            original_pdf_url=bid.original_pdf_url or target_url,
            original_pdf_checksum=doc_checksum,
            document_version=bid.document_version or "1.0",
            original_publication_date=bid.original_publication_date or bid.start_date,
            original_deadline=bid.original_end_date or bid.end_date,
            latest_revised_deadline=bid.revised_end_date or bid.end_date,
            corrigendum_reference=bid.corrigendum_reference,
            corrigendum_date=bid.corrigendum_date,
            corrigendum_status=bid.corrigendum_status or "NONE",
            latest_verified_status=bid.bid_status or "ACTIVE",
            raw_extracted_text=bid.raw_extracted_text,
            extracted_category=bid.extracted_category or bid.category_name,
            extracted_consignee_name=bid.extracted_consignee_name or bid.pdf_delivery_consignee,
            extracted_delivery_address=bid.extracted_delivery_address or bid.pdf_delivery_address,
            extracted_city=bid.extracted_city or bid.pdf_delivery_city,
            extracted_district=bid.extracted_district or bid.pdf_delivery_district,
            extracted_state=bid.extracted_state or bid.pdf_delivery_state,
            extracted_pincode=bid.extracted_pincode or bid.pdf_delivery_pincode,
            pdf_details_page_number=bid.pdf_details_page_number or 1,
            pdf_consignee_page_number=bid.pdf_page_number,
            extraction_timestamp=bid.extraction_timestamp or bid.pdf_processed_at,
            verification_timestamp=bid.verification_timestamp,
            data_confidence=bid.data_confidence or bid.pdf_confidence_score or 0.9,
            synchronization_status=STATUS_VERIFIED,
            target_location_status=bid.target_location_status,
            verification_reason=bid.verification_reason or "Verified against cached PDF evidence.",
        )

    # 3. Read and Parse PDF
    try:
        stream = io.BytesIO(raw_content)
        reader = PdfReader(stream)
        total_pages = len(reader.pages)
        if total_pages == 0:
            raise ValueError("PDF contains 0 pages.")
    except Exception as e:
        reason = f"OCR_UNCERTAIN: PDF document corrupted or unreadable: {e}"
        logger.error(f"Failed to read PDF for bid {bid.bid_number}: {e}")
        res = PdfSyncResult(
            bid_id=bid.id,
            bid_number=bid.bid_number,
            original_pdf_checksum=doc_checksum,
            synchronization_status=STATUS_OCR_UNCERTAIN,
            latest_verified_status="UNKNOWN",
            target_location_status=STATUS_UNKNOWN,
            extraction_timestamp=now_utc,
            verification_timestamp=now_utc,
            verification_reason=reason,
            error_message=reason,
        )
        if db:
            bid.synchronization_status = STATUS_OCR_UNCERTAIN
            bid.pdf_verification_status = "PDF_UNAVAILABLE"
            bid.target_location_status = STATUS_UNKNOWN
            bid.verification_reason = reason
            bid.verification_timestamp = now_utc
            try:
                db.commit()
            except Exception:
                db.rollback()
        return res

    # 4. Extract Page 1 Header Metadata
    page_1_text = reader.pages[0].extract_text() or ""
    raw_snippet = page_1_text[:2000].strip()
    p1_meta = extract_metadata_from_page_1(page_1_text)

    pdf_bid_no = p1_meta.get("pdf_bid_number")
    dated_str = p1_meta.get("dated_str")
    end_date_str = p1_meta.get("end_date_str")
    category_str = p1_meta.get("category_str")

    # If bid number not on Page 1, check first 3 pages
    if not pdf_bid_no:
        for p_idx in range(1, min(3, total_pages)):
            extra_text = reader.pages[p_idx].extract_text() or ""
            extra_m = re.search(r"\b(GEM/\d{4}/[A-Z]/\d+)\b", extra_text)
            if extra_m:
                pdf_bid_no = extra_m.group(1).strip()
                break

    # 5. Fail-Closed Check: Bid Number Identity Match
    if not pdf_bid_no:
        reason = "OCR_UNCERTAIN: Bid number not found inside PDF document; cannot guarantee document identity."
        logger.warning(f"Bid {bid.bid_number}: {reason}")
        res = PdfSyncResult(
            bid_id=bid.id,
            bid_number=bid.bid_number,
            pdf_bid_number=None,
            is_bid_matched=False,
            official_source_url=target_url,
            original_pdf_url=target_url,
            original_pdf_checksum=doc_checksum,
            raw_extracted_text=raw_snippet,
            synchronization_status=STATUS_OCR_UNCERTAIN,
            latest_verified_status="UNKNOWN",
            target_location_status=STATUS_AMBIGUOUS,
            extraction_timestamp=now_utc,
            verification_timestamp=now_utc,
            verification_reason=reason,
            error_message=reason,
        )
        if db:
            bid.synchronization_status = STATUS_OCR_UNCERTAIN
            bid.pdf_verification_status = "AMBIGUOUS"
            bid.target_location_status = STATUS_AMBIGUOUS
            bid.verification_reason = reason
            bid.verification_timestamp = now_utc
            try:
                db.commit()
            except Exception:
                db.rollback()
        return res

    clean_pdf_bid = pdf_bid_no.strip().upper()
    clean_expected_bid = bid.bid_number.strip().upper()
    is_bid_matched = (clean_pdf_bid == clean_expected_bid)

    # 6. Fail-Closed Check: PDF_BID_MISMATCH or DOCUMENT_VERSION_MISMATCH
    if not is_bid_matched:
        # Check if year differs (e.g. 2025 vs 2026)
        pdf_year_m = re.search(r"/(\d{4})/", clean_pdf_bid)
        expected_year_m = re.search(r"/(\d{4})/", clean_expected_bid)
        status_code = STATUS_PDF_BID_MISMATCH
        if pdf_year_m and expected_year_m and pdf_year_m.group(1) != expected_year_m.group(1):
            status_code = STATUS_DOCUMENT_VERSION_MISMATCH

        # Extract address evidence from PDF to document the mismatch (e.g. Nadiad, Gujarat)
        loc_evidence: ExtractedDeliveryLocation = extract_location_from_pdf(pdf_bytes=raw_content)
        loc_str = f" in {loc_evidence.state or 'Outside'} ({loc_evidence.city or 'Unknown'}, PIN: {loc_evidence.pincode or 'N/A'})" if loc_evidence.state else ""

        reason = (
            f"{status_code}: Document identity failure. PDF contains '{pdf_bid_no}'{loc_str}, "
            f"which does not match registered bid '{bid.bid_number}'. Quarantined in Review Queue."
        )
        logger.warning(reason)

        res = PdfSyncResult(
            bid_id=bid.id,
            bid_number=bid.bid_number,
            pdf_bid_number=pdf_bid_no,
            is_bid_matched=False,
            official_source_url=target_url,
            original_pdf_url=target_url,
            original_pdf_checksum=doc_checksum,
            raw_extracted_text=raw_snippet,
            extracted_delivery_address=loc_evidence.full_address,
            extracted_city=loc_evidence.city,
            extracted_district=loc_evidence.district,
            extracted_state=loc_evidence.state,
            extracted_pincode=loc_evidence.pincode,
            synchronization_status=status_code,
            latest_verified_status="DATA_MISMATCH",
            target_location_status=STATUS_AMBIGUOUS,  # Strictly Quarantined
            extraction_timestamp=now_utc,
            verification_timestamp=now_utc,
            verification_reason=reason,
            error_message=reason,
        )
        if db:
            bid.synchronization_status = status_code
            bid.pdf_verification_status = status_code
            bid.target_location_status = STATUS_AMBIGUOUS
            bid.pdf_bid_number = pdf_bid_no
            bid.original_pdf_checksum = doc_checksum
            bid.raw_extracted_text = raw_snippet
            bid.extracted_delivery_address = loc_evidence.full_address
            bid.extracted_city = loc_evidence.city
            bid.extracted_district = loc_evidence.district
            bid.extracted_state = loc_evidence.state
            bid.extracted_pincode = loc_evidence.pincode
            # Overwrite pdf_delivery_* with true extracted evidence so fake data is wiped out
            bid.pdf_delivery_address = loc_evidence.full_address
            bid.pdf_delivery_city = loc_evidence.city
            bid.pdf_delivery_district = loc_evidence.district
            bid.pdf_delivery_state = loc_evidence.state
            bid.pdf_delivery_pincode = loc_evidence.pincode
            bid.pdf_page_number = loc_evidence.page_number
            bid.verification_reason = reason
            bid.verification_timestamp = now_utc
            try:
                db.commit()
            except Exception:
                db.rollback()
        return res

    # 7. Document Identity Confirmed -> Extract Delivery Location from Actual PDF Evidence
    loc_ext: ExtractedDeliveryLocation = extract_location_from_pdf(pdf_bytes=raw_content)

    # 8. Fail-Closed Check: Location Mismatch (e.g. Gujarat, Dehradun, Rajasthan, or Bengaluru Rural)
    pdf_state_clean = (loc_ext.state or "").upper().strip()
    pdf_dist_clean = (loc_ext.district or "").lower().strip()
    pdf_city_clean = (loc_ext.city or "").lower().strip()

    is_outside_state = bool(pdf_state_clean and pdf_state_clean != "KARNATAKA")
    is_rural = bool("rural" in pdf_dist_clean or "rural" in pdf_city_clean)

    if is_outside_state or is_rural:
        reason = (
            f"LOCATION_MISMATCH: Actual PDF evidence indicates delivery in {loc_ext.state} "
            f"({loc_ext.city or loc_ext.district or 'Outside'}, PIN: {loc_ext.pincode or 'N/A'}), "
            f"which is outside Bengaluru Urban / City."
        )
        logger.warning(f"Bid {bid.bid_number}: {reason}")
        res = PdfSyncResult(
            bid_id=bid.id,
            bid_number=bid.bid_number,
            pdf_bid_number=pdf_bid_no,
            is_bid_matched=True,
            official_source_url=target_url,
            original_pdf_url=target_url,
            original_pdf_checksum=doc_checksum,
            raw_extracted_text=raw_snippet,
            extracted_category=category_str or bid.category_name,
            extracted_consignee_name=loc_ext.consignee_name,
            extracted_delivery_address=loc_ext.full_address,
            extracted_city=loc_ext.city,
            extracted_district=loc_ext.district,
            extracted_state=loc_ext.state,
            extracted_pincode=loc_ext.pincode,
            synchronization_status=STATUS_LOCATION_MISMATCH,
            latest_verified_status="LOCATION_MISMATCH",
            target_location_status=STATUS_OUTSIDE_TARGET,
            extraction_timestamp=now_utc,
            verification_timestamp=now_utc,
            verification_reason=reason,
            error_message=reason,
        )
        if db:
            bid.synchronization_status = STATUS_LOCATION_MISMATCH
            bid.pdf_verification_status = STATUS_LOCATION_MISMATCH
            bid.target_location_status = STATUS_OUTSIDE_TARGET
            bid.pdf_bid_number = pdf_bid_no
            bid.original_pdf_checksum = doc_checksum
            bid.raw_extracted_text = raw_snippet
            bid.extracted_delivery_address = loc_ext.full_address
            bid.extracted_city = loc_ext.city
            bid.extracted_district = loc_ext.district
            bid.extracted_state = loc_ext.state
            bid.extracted_pincode = loc_ext.pincode
            bid.verification_reason = reason
            bid.verification_timestamp = now_utc
            try:
                db.commit()
            except Exception:
                db.rollback()
        return res

    # 9. Evaluate Corrigenda & Dates
    pdf_pub_date = parse_gem_ist_datetime(dated_str) if dated_str else None
    pdf_end_date = parse_gem_ist_datetime(end_date_str) if end_date_str else None

    orig_deadline = pdf_end_date or bid.original_end_date or bid.end_date
    rev_deadline = bid.revised_end_date
    corr_status = bid.corrigendum_status or "NONE"

    effective_deadline = rev_deadline or orig_deadline
    bid_life_status = calculate_bid_status(effective_deadline, bid.status or 1, now_utc=now_utc)

    # Evaluate target location classification
    bid_eval_dict = {
        "pdf_delivery_city": loc_ext.city,
        "pdf_delivery_district": loc_ext.district,
        "pdf_delivery_state": loc_ext.state,
        "pdf_delivery_address": loc_ext.full_address,
        "pdf_delivery_pincode": loc_ext.pincode,
        "consignee_city": bid.consignee_city,
        "consignee_district": bid.consignee_district,
        "consignee_state": bid.consignee_state,
        "buyer_city": bid.buyer_city,
        "buyer_district": bid.buyer_district,
        "buyer_state": bid.buyer_state,
    }
    t_status, conf, eff_city, eff_dist, eff_state = resolve_effective_bid_delivery_location(bid_eval_dict)

    # 10. Fail-Closed Gate: Is Location Genuinely Verified in Complete Bengaluru Region?
    if t_status not in (STATUS_VERIFIED_BENGALURU_URBAN, STATUS_VERIFIED_BENGALURU_RURAL, STATUS_VERIFIED_BENGALURU_CITY):
        reason = f"OCR_UNCERTAIN: Delivery address '{loc_ext.full_address[:100]}' could not be definitively validated in Bengaluru Urban, Rural, or City."
        sync_status = STATUS_OCR_UNCERTAIN
    else:
        sync_status = STATUS_VERIFIED
        reason = "VERIFIED: Bid number, document identity, dates, and Bengaluru delivery address verified against official PDF."

    final_conf = max(conf, loc_ext.confidence_score)

    res = PdfSyncResult(
        bid_id=bid.id,
        bid_number=bid.bid_number,
        pdf_bid_number=pdf_bid_no,
        is_bid_matched=True,
        official_source_url=target_url,
        original_pdf_url=target_url,
        original_pdf_checksum=doc_checksum,
        document_version="1.0",
        original_publication_date=pdf_pub_date or bid.start_date,
        original_deadline=orig_deadline,
        latest_revised_deadline=rev_deadline,
        corrigendum_reference=bid.corrigendum_details,
        corrigendum_date=bid.corrigendum_date,
        corrigendum_status=corr_status,
        latest_verified_status=bid_life_status,
        raw_extracted_text=raw_snippet,
        extracted_category=category_str or bid.category_name,
        extracted_consignee_name=loc_ext.consignee_name,
        extracted_delivery_address=loc_ext.full_address,
        extracted_city=loc_ext.city or eff_city,
        extracted_district=loc_ext.district or eff_dist,
        extracted_state=loc_ext.state or eff_state,
        extracted_pincode=loc_ext.pincode,
        pdf_details_page_number=1,
        pdf_consignee_page_number=loc_ext.page_number,
        extraction_timestamp=now_utc,
        verification_timestamp=now_utc,
        data_confidence=final_conf,
        synchronization_status=sync_status,
        target_location_status=t_status,
        verification_reason=reason,
    )

    if db:
        bid.official_source_url = res.official_source_url
        bid.original_pdf_url = res.original_pdf_url
        bid.original_pdf_checksum = res.original_pdf_checksum
        bid.pdf_doc_hash = res.original_pdf_checksum
        bid.document_version = res.document_version
        if res.original_publication_date and not bid.original_publication_date:
            bid.original_publication_date = res.original_publication_date
            if not bid.start_date:
                bid.start_date = res.original_publication_date

        if res.original_deadline and not bid.original_end_date:
            bid.original_end_date = res.original_deadline

        if res.latest_revised_deadline:
            bid.revised_end_date = res.latest_revised_deadline
            bid.end_date = res.latest_revised_deadline
        elif res.original_deadline and not bid.end_date:
            bid.end_date = res.original_deadline

        bid.raw_extracted_text = res.raw_extracted_text
        bid.extracted_category = res.extracted_category
        bid.extracted_consignee_name = res.extracted_consignee_name
        bid.extracted_delivery_address = res.extracted_delivery_address
        bid.extracted_city = res.extracted_city
        bid.extracted_district = res.extracted_district
        bid.extracted_state = res.extracted_state
        bid.extracted_pincode = res.extracted_pincode

        bid.pdf_delivery_address = res.extracted_delivery_address
        bid.pdf_delivery_city = res.extracted_city
        bid.pdf_delivery_district = res.extracted_district
        bid.pdf_delivery_state = res.extracted_state
        bid.pdf_delivery_pincode = res.extracted_pincode
        bid.pdf_delivery_consignee = res.extracted_consignee_name
        bid.pdf_page_number = res.pdf_consignee_page_number
        bid.pdf_details_page_number = res.pdf_details_page_number
        bid.pdf_confidence_score = res.data_confidence
        bid.pdf_verification_status = sync_status
        bid.pdf_processed_at = now_utc

        bid.pdf_bid_number = res.pdf_bid_number
        bid.extraction_timestamp = now_utc
        bid.verification_timestamp = now_utc
        bid.data_confidence = res.data_confidence
        bid.synchronization_status = res.synchronization_status
        bid.target_location_status = res.target_location_status
        bid.bid_status = res.latest_verified_status
        bid.verification_reason = res.verification_reason

        try:
            db.commit()
            db.refresh(bid)
        except Exception as dbe:
            db.rollback()
            logger.error(f"Failed to commit synchronized bid {bid.bid_number}: {dbe}")

    return res
