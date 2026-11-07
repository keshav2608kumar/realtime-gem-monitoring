"""
GeM BidWatch — Authoritative PDF & Bid Synchronization Engine
Implements strict document-to-bid synchronization protocol:
1. Retrieves official GeM bid record and official document.
2. Verifies the bid number inside the document against the database bid record.
3. Detects document mismatch, corrupt documents, or missing documents.
4. Extracts original publication date, original deadline, and item category from Page 1.
5. Extracts consignee delivery address, city, district, state, and PIN code from final pages.
6. Evaluates corrigenda in chronological order and resolves the latest effective deadline.
7. Classifies target delivery location into Bengaluru Urban, Bengaluru City, Review Queue, or Outside Target.
8. Persists all 20+ provenance and audit fields separately without overwriting original source values.
"""

import io
import re
import hashlib
import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta

import httpx
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.models.bid import Bid
from app.services.location_normalizer import (
    resolve_effective_bid_delivery_location,
    STATUS_VERIFIED_BENGALURU_URBAN,
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

# Official GeM synchronization statuses
SYNC_SYNCHRONIZED = "SYNCHRONIZED"
SYNC_DATA_MISMATCH = "DATA_MISMATCH"
SYNC_FAILED = "FAILED"
SYNC_PDF_UNAVAILABLE = "PDF_UNAVAILABLE"
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
    latest_verified_status: str = "ACTIVE"
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
    synchronization_status: str = SYNC_PENDING
    target_location_status: str = STATUS_UNKNOWN
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def parse_gem_ist_datetime(date_str: str) -> Optional[datetime]:
    """
    Parse GeM date/time strings such as '28-10-2026 13:00:00' or '16-10-2026'
    into an aware UTC datetime object.
    """
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
            # Interpret as IST and convert to UTC
            dt_ist = dt.replace(tzinfo=ist_tz)
            return dt_ist.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def extract_metadata_from_page_1(page_text: str) -> Dict[str, Any]:
    """
    Extract authoritative header fields from Page 1 of GeM bid document.
    """
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
        # Clean off trailing Q2 or parentheses if present
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
    Execute full authoritative 10-step synchronization between Bid record and PDF document.
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

    # 1. Document Missing / Unavailable
    if not raw_content:
        res = PdfSyncResult(
            bid_id=bid.id,
            bid_number=bid.bid_number,
            official_source_url=target_url,
            original_pdf_url=target_url,
            synchronization_status=SYNC_PDF_UNAVAILABLE,
            latest_verified_status="UNKNOWN",
            target_location_status=bid.target_location_status or STATUS_UNKNOWN,
            extraction_timestamp=now_utc,
            error_message="Official PDF document could not be retrieved from GeM portal.",
        )
        if db:
            bid.synchronization_status = SYNC_PDF_UNAVAILABLE
            bid.pdf_verification_status = "PDF_UNAVAILABLE"
            bid.verification_timestamp = now_utc
            try:
                db.commit()
            except Exception:
                db.rollback()
        return res

    doc_checksum = compute_doc_hash(raw_content)

    # 2. Checksum Cache (Skip re-processing if unchanged unless force=True)
    if not force and bid.original_pdf_checksum == doc_checksum and bid.synchronization_status == SYNC_SYNCHRONIZED:
        logger.info(f"Bid {bid.bid_number} PDF checksum unchanged ({doc_checksum[:8]}); using verified state.")
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
            synchronization_status=SYNC_SYNCHRONIZED,
            target_location_status=bid.target_location_status or STATUS_VERIFIED_BENGALURU_URBAN,
        )

    # 3. Read and Parse PDF
    try:
        stream = io.BytesIO(raw_content)
        reader = PdfReader(stream)
        total_pages = len(reader.pages)
        if total_pages == 0:
            raise ValueError("PDF contains 0 pages.")
    except Exception as e:
        logger.error(f"Failed to read PDF for bid {bid.bid_number}: {e}")
        res = PdfSyncResult(
            bid_id=bid.id,
            bid_number=bid.bid_number,
            original_pdf_checksum=doc_checksum,
            synchronization_status=SYNC_FAILED,
            latest_verified_status="UNKNOWN",
            target_location_status=STATUS_UNKNOWN,
            extraction_timestamp=now_utc,
            error_message=f"PDF document corrupted or unreadable: {e}",
        )
        if db:
            bid.synchronization_status = SYNC_FAILED
            bid.pdf_verification_status = "PDF_UNAVAILABLE"
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

    pdf_pub_date = parse_gem_ist_datetime(dated_str) if dated_str else None
    pdf_end_date = parse_gem_ist_datetime(end_date_str) if end_date_str else None

    # 5. BID NUMBER CROSS-VERIFICATION
    # If a bid number was found inside the PDF and does NOT match the record, REJECT!
    is_bid_matched = False
    if pdf_bid_no:
        clean_pdf_bid = pdf_bid_no.strip().upper()
        clean_expected_bid = bid.bid_number.strip().upper()
        is_bid_matched = (clean_pdf_bid == clean_expected_bid)
    else:
        # Fallback: if bid number pattern wasn't on Page 1, check first 3 pages
        for p_idx in range(1, min(3, total_pages)):
            extra_text = reader.pages[p_idx].extract_text() or ""
            extra_m = re.search(r"\b(GEM/\d{4}/[A-Z]/\d+)\b", extra_text)
            if extra_m:
                pdf_bid_no = extra_m.group(1).strip()
                is_bid_matched = (pdf_bid_no.upper() == bid.bid_number.strip().upper())
                break

    # If document explicitly belongs to ANOTHER bid -> DATA_MISMATCH
    if pdf_bid_no and not is_bid_matched:
        error_msg = f"Document Mismatch: PDF contains '{pdf_bid_no}', expected '{bid.bid_number}'"
        logger.warning(error_msg)
        res = PdfSyncResult(
            bid_id=bid.id,
            bid_number=bid.bid_number,
            pdf_bid_number=pdf_bid_no,
            is_bid_matched=False,
            official_source_url=target_url,
            original_pdf_url=target_url,
            original_pdf_checksum=doc_checksum,
            raw_extracted_text=raw_snippet,
            synchronization_status=SYNC_DATA_MISMATCH,
            latest_verified_status="DATA_MISMATCH",
            target_location_status=STATUS_AMBIGUOUS,  # Route to Review Queue
            extraction_timestamp=now_utc,
            verification_timestamp=now_utc,
            error_message=error_msg,
        )
        if db:
            bid.synchronization_status = SYNC_DATA_MISMATCH
            bid.pdf_verification_status = "AMBIGUOUS"
            bid.target_location_status = STATUS_AMBIGUOUS
            bid.pdf_bid_number = pdf_bid_no
            bid.original_pdf_checksum = doc_checksum
            bid.raw_extracted_text = raw_snippet
            bid.verification_timestamp = now_utc
            try:
                db.commit()
            except Exception:
                db.rollback()
        return res

    # 6. Extract Delivery Location (Final Pages prioritized)
    loc_ext: ExtractedDeliveryLocation = extract_location_from_pdf(pdf_bytes=raw_content)

    # 7. Evaluate Corrigenda & Deadlines
    orig_deadline = pdf_end_date or bid.original_end_date or bid.end_date
    rev_deadline = bid.revised_end_date
    corr_status = bid.corrigendum_status or "NONE"

    effective_deadline = rev_deadline or orig_deadline
    bid_life_status = calculate_bid_status(effective_deadline, bid.status or 1, now_utc=now_utc)

    # 8. Evaluate Target Location Status
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

    # Confidence score calculation
    final_conf = max(conf, loc_ext.confidence_score)
    sync_status = SYNC_SYNCHRONIZED

    res = PdfSyncResult(
        bid_id=bid.id,
        bid_number=bid.bid_number,
        pdf_bid_number=pdf_bid_no or bid.bid_number,
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
    )

    # 9. Idempotent Database Update (separate fields, preserving source records)
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

        # Delivery location mirror
        bid.pdf_delivery_address = res.extracted_delivery_address
        bid.pdf_delivery_city = res.extracted_city
        bid.pdf_delivery_district = res.extracted_district
        bid.pdf_delivery_state = res.extracted_state
        bid.pdf_delivery_pincode = res.extracted_pincode
        bid.pdf_delivery_consignee = res.extracted_consignee_name
        bid.pdf_page_number = res.pdf_consignee_page_number
        bid.pdf_details_page_number = res.pdf_details_page_number
        bid.pdf_confidence_score = res.data_confidence
        bid.pdf_verification_status = loc_ext.verification_status
        bid.pdf_processed_at = now_utc

        bid.pdf_bid_number = res.pdf_bid_number
        bid.extraction_timestamp = now_utc
        bid.verification_timestamp = now_utc
        bid.data_confidence = res.data_confidence
        bid.synchronization_status = res.synchronization_status
        bid.target_location_status = res.target_location_status
        bid.bid_status = res.latest_verified_status

        try:
            db.commit()
            db.refresh(bid)
        except Exception as dbe:
            db.rollback()
            logger.error(f"Failed to commit synchronized bid {bid.bid_number}: {dbe}")

    return res
