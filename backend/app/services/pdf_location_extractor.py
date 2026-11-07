"""
GeM BidWatch — PDF Delivery Location Extraction Engine
Inspects official GeM Bid PDF documents, prioritizing the final pages,
to extract structured delivery/consignee address, PIN code, and administrative location.

Follows strict GeM procurement document parsing rules:
- Prioritizes the final pages where the 'Consignees/Reporting Officer and Quantity' table is placed.
- Extracts Recipient, Organization, Building, Street, City, District, State, and PIN code.
- Segregates Buyer vs Consignee vs Delivery locations.
- Performs checksum/hash caching to avoid redundant processing.
"""
import io
import re
import hashlib
import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

import httpx
from pypdf import PdfReader

from app.services.location_normalizer import (
    resolve_state, clean_text, CITY_DISTRICT_TO_STATE, CANONICAL_STATES
)

logger = logging.getLogger(__name__)

# Postal Index Number (PIN) first 2 digits to state validation mapping
PIN_PREFIX_TO_STATE = {
    "11": "DELHI",
    "12": "HARYANA", "13": "HARYANA",
    "14": "PUNJAB", "15": "PUNJAB", "16": "PUNJAB",
    "17": "HIMACHAL PRADESH",
    "18": "JAMMU & KASHMIR", "19": "JAMMU & KASHMIR",
    "20": "UTTAR PRADESH", "21": "UTTAR PRADESH", "22": "UTTAR PRADESH",
    "23": "UTTAR PRADESH", "24": "UTTAR PRADESH", "25": "UTTAR PRADESH",
    "26": "UTTAR PRADESH", "27": "UTTAR PRADESH", "28": "UTTAR PRADESH",
    "30": "RAJASTHAN", "31": "RAJASTHAN", "32": "RAJASTHAN", "33": "RAJASTHAN", "34": "RAJASTHAN",
    "36": "GUJARAT", "37": "GUJARAT", "38": "GUJARAT", "39": "GUJARAT",
    "40": "MAHARASHTRA", "41": "MAHARASHTRA", "42": "MAHARASHTRA", "43": "MAHARASHTRA", "44": "MAHARASHTRA",
    "45": "MADHYA PRADESH", "46": "MADHYA PRADESH", "47": "MADHYA PRADESH", "48": "MADHYA PRADESH",
    "49": "CHHATTISGARH",
    "50": "TELANGANA", "51": "ANDHRA PRADESH", "52": "ANDHRA PRADESH", "53": "ANDHRA PRADESH",
    "56": "KARNATAKA", "57": "KARNATAKA", "58": "KARNATAKA", "59": "KARNATAKA",
    "60": "TAMIL NADU", "61": "TAMIL NADU", "62": "TAMIL NADU", "63": "TAMIL NADU", "64": "TAMIL NADU",
    "67": "KERALA", "68": "KERALA", "69": "KERALA",
    "70": "WEST BENGAL", "71": "WEST BENGAL", "72": "WEST BENGAL", "73": "WEST BENGAL", "74": "WEST BENGAL",
    "75": "ODISHA", "76": "ODISHA", "77": "ODISHA",
    "78": "ASSAM", "79": "ASSAM",
    "80": "BIHAR", "81": "BIHAR", "82": "BIHAR", "83": "JHARKHAND", "84": "BIHAR", "85": "BIHAR",
}

# Common designations for GeM consignees / reporting officers
CONSIGNEE_DESIGNATION_PATTERNS = [
    r"\b(?:stores?\s*officer|procurement\s*officer|commanding\s*officer|administrative\s*officer)\b",
    r"\b(?:senior\s*manager|general\s*manager|executive\s*engineer|assistant\s*engineer)\b",
    r"\b(?:director|dean|principal|superintendent|incharge|in-charge|head\s*of\s*office)\b",
    r"\b(?:scientist|commandant|major|colonel|lieutenant|captain|registrar)\b",
]


@dataclass
class ExtractedDeliveryLocation:
    consignee_name: Optional[str] = None
    organization: Optional[str] = None
    building_campus: Optional[str] = None
    street_locality: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    full_address: str = ""
    page_number: Optional[int] = None
    total_pages: Optional[int] = None
    extraction_method: str = "PDF_TEXT"
    confidence_score: float = 0.0
    verification_status: str = "UNKNOWN"
    doc_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def compute_doc_hash(content: bytes) -> str:
    """Generate SHA256 checksum of document bytes."""
    return hashlib.sha256(content).hexdigest()


def fetch_pdf_bytes(url: str, timeout: float = 12.0) -> Optional[bytes]:
    """Download PDF bytes using standard browser headers with fallback handling."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "application/pdf,*/*",
        "Referer": "https://bidplus.gem.gov.in/",
    }
    try:
        with httpx.Client(headers=headers, timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url)
            if resp.status_code == 200 and len(resp.content) > 100:
                return resp.content
            logger.warning(f"PDF download returned status {resp.status_code} for {url}")
            return None
    except Exception as e:
        logger.warning(f"Failed to download PDF from {url}: {e}")
        return None


def extract_pincode(text: str) -> Optional[str]:
    """Extract a valid 6-digit Indian PIN code."""
    # Matches 6 consecutive digits with standard word/delimiter boundaries
    matches = re.findall(r"(?:^|[^\d])([1-9][0-9]{5})(?:[^\d]|$)", text)
    if matches:
        return matches[0]
    return None


def identify_state_from_text(text: str) -> Optional[str]:
    """Identify recognized canonical Indian state name from text."""
    text_clean = clean_text(text)
    # Check directly via resolve_state
    st = resolve_state(text_clean)
    if st:
        return st

    # Word boundary match for canonical states
    text_lower = text_clean.lower()
    for canonical in CANONICAL_STATES:
        pattern = r"\b" + re.escape(canonical.lower()) + r"\b"
        if re.search(pattern, text_lower):
            return canonical

    return None


def identify_city_and_district(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Scan text against known cities and return (city, district, implied_state)."""
    text_lower = clean_text(text).lower()
    for city_key, (c_name, dist_name, state_name) in CITY_DISTRICT_TO_STATE.items():
        pattern = r"\b" + re.escape(city_key) + r"\b"
        if re.search(pattern, text_lower):
            return c_name, dist_name, state_name
    return None, None, None


def parse_consignee_block(
    page_text: str,
    page_num: int,
    total_pages: int
) -> Optional[ExtractedDeliveryLocation]:
    """
    Parse a single page for GeM consignee/delivery address structures.
    Looks for the 'Consignees/Reporting Officer and Quantity' table or 'Consignee / Delivery Address'.
    """
    if not page_text or len(page_text.strip()) < 20:
        return None

    # Key trigger markers used by GeM
    markers = [
        r"consignees?\s*/?\s*reporting\s*officer\s*(?:and\s*quantity)?",
        r"consignee\s*/?\s*delivery\s*address",
        r"consignee\s*details",
        r"delivery\s*location",
        r"delivery\s*address",
    ]

    has_marker = any(re.search(p, page_text, re.IGNORECASE) for p in markers)

    # If the page does not explicitly have the table marker, check if it's the last page
    # and contains an address with PIN code and state
    pincode = extract_pincode(page_text)
    state = identify_state_from_text(page_text)
    city, district, implied_state = identify_city_and_district(page_text)

    if not has_marker and not (pincode and (state or implied_state)):
        return None

    final_state = state or implied_state

    # Verify PIN code with state postal region if available
    pin_state = None
    if pincode:
        pin_prefix = pincode[:2]
        pin_state = PIN_PREFIX_TO_STATE.get(pin_prefix)

    # Isolate relevant address lines around the consignee section or around the PIN code
    lines = [line.strip() for line in page_text.splitlines() if line.strip()]
    address_lines = []
    capture = False
    consignee_name = None
    organization = None

    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(re.search(p, line_lower) for p in markers):
            capture = True
            continue

        if capture:
            # Table headers to skip
            if re.search(r"^\s*s\.?\s*no\.?\s*|consignee\s*/|delivery\s*days", line_lower):
                continue
            # End of section triggers
            if re.search(r"buyer\s*added\s*bid\s*specific|eligibility\s*criteria|terms\s*and\s*conditions", line_lower):
                break

            # Check for designation or officer
            for des_pat in CONSIGNEE_DESIGNATION_PATTERNS:
                if re.search(des_pat, line, re.IGNORECASE) and not consignee_name:
                    consignee_name = line
                    break

            # Check for table row format: "1 <Name/Designation> <PIN/Address>"
            if not consignee_name:
                row_m = re.search(r"^\s*\d+\s+([A-Za-z\s\.\(\)\-]+?)\s+(?:[1-9][0-9]{5}|address)", line, re.IGNORECASE)
                if row_m:
                    candidate_name = row_m.group(1).strip()
                    if len(candidate_name) >= 3 and not re.search(r"^(?:s\.?no|consignee|address)", candidate_name, re.IGNORECASE):
                        consignee_name = candidate_name

            # Look for institution/organization
            if re.search(r"\b(?:institute|university|hospital|drdo|isro|command|centre|station|school|college|division|dept|railways)\b", line, re.IGNORECASE):
                if not organization:
                    organization = line

            address_lines.append(line)
            # Stop capturing after 6 lines or after finding PIN code line
            if len(address_lines) >= 6 or (pincode and pincode in line):
                if len(address_lines) >= 3:
                    break

    # If table markers weren't used but PIN code was found, locate lines surrounding PIN
    if not address_lines and pincode:
        for idx, line in enumerate(lines):
            if pincode in line:
                start_idx = max(0, idx - 2)
                end_idx = min(len(lines), idx + 3)
                address_lines = lines[start_idx:end_idx]
                break

    full_address = ", ".join(address_lines) if address_lines else page_text[:300].strip()

    # Determine verification status and confidence score
    confidence = 0.0
    status = "UNKNOWN"

    # Rule 1: High verification — City, State, and PIN code matching the postal zone
    if city and final_state and pincode and pin_state == final_state:
        confidence = 0.95
        status = "VERIFIED"
    # Rule 2: Verified — City, State, and PIN code present
    elif city and final_state and pincode:
        confidence = 0.88
        status = "VERIFIED"
    # Rule 3: Partially Verified — City and State identified without full PIN validation
    elif city and final_state:
        confidence = 0.75
        status = "PARTIALLY_VERIFIED"
    # Rule 4: State or City identified from PIN code alone
    elif pincode and pin_state:
        confidence = 0.60
        status = "PARTIALLY_VERIFIED"
        if not final_state:
            final_state = pin_state
    # Rule 5: Ambiguous / Low confidence
    elif city or final_state:
        confidence = 0.40
        status = "AMBIGUOUS"
    else:
        confidence = 0.10
        status = "UNKNOWN"

    return ExtractedDeliveryLocation(
        consignee_name=consignee_name,
        organization=organization,
        building_campus=organization,
        street_locality=city,
        city=city,
        district=district or city,
        state=final_state,
        pincode=pincode,
        full_address=full_address,
        page_number=page_num,
        total_pages=total_pages,
        extraction_method="PDF_TEXT",
        confidence_score=confidence,
        verification_status=status,
    )


def extract_location_from_pdf(
    pdf_bytes: Optional[bytes] = None,
    pdf_path: Optional[str] = None,
    pdf_url: Optional[str] = None,
) -> ExtractedDeliveryLocation:
    """
    Main extraction interface.
    Accepts raw PDF bytes, a local file path, or an official GeM URL.
    Scans the document prioritizing the final pages first.
    """
    raw_content: Optional[bytes] = None

    if pdf_bytes:
        raw_content = pdf_bytes
    elif pdf_path:
        try:
            with open(pdf_path, "rb") as f:
                raw_content = f.read()
        except Exception as e:
            logger.warning(f"Could not read local PDF at {pdf_path}: {e}")
    elif pdf_url:
        raw_content = fetch_pdf_bytes(pdf_url)

    if not raw_content:
        return ExtractedDeliveryLocation(
            verification_status="PDF_UNAVAILABLE",
            extraction_method="PDF_TEXT",
            confidence_score=0.0,
            full_address="Delivery address could not be verified from the available document."
        )

    doc_hash = compute_doc_hash(raw_content)

    try:
        stream = io.BytesIO(raw_content)
        reader = PdfReader(stream)
        total_pages = len(reader.pages)

        if total_pages == 0:
            return ExtractedDeliveryLocation(
                verification_status="PDF_UNAVAILABLE",
                doc_hash=doc_hash,
                full_address="Delivery address could not be verified from the available document."
            )

        # ─── PRIORITIZE FINAL PAGES FIRST ──────────────────────────────────
        # GeM standard: Consignee and delivery address details reside in the last pages.
        # Order of inspection: Last page, penultimate page, 3rd from last, then backwards.
        prioritized_indices: List[int] = []
        for offset in range(1, min(4, total_pages + 1)):
            prioritized_indices.append(total_pages - offset)

        # Remaining earlier pages if needed
        for p_idx in range(total_pages - 4, -1, -1):
            prioritized_indices.append(p_idx)

        candidates: List[ExtractedDeliveryLocation] = []

        for p_idx in prioritized_indices:
            try:
                page = reader.pages[p_idx]
                page_text = page.extract_text() or ""
                extracted = parse_consignee_block(page_text, page_num=p_idx + 1, total_pages=total_pages)
                if extracted:
                    extracted.doc_hash = doc_hash
                    # If high-confidence verified match found in final pages, return immediately
                    if extracted.verification_status == "VERIFIED" and extracted.confidence_score >= 0.85:
                        return extracted
                    candidates.append(extracted)
            except Exception as pe:
                logger.debug(f"Notice on page {p_idx}: {pe}")

        if candidates:
            # Pick candidate with highest confidence score
            best = max(candidates, key=lambda c: c.confidence_score)
            return best

        return ExtractedDeliveryLocation(
            verification_status="UNKNOWN",
            total_pages=total_pages,
            doc_hash=doc_hash,
            full_address="Delivery address could not be verified from the available document."
        )

    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}", exc_info=True)
        return ExtractedDeliveryLocation(
            verification_status="PDF_UNAVAILABLE",
            doc_hash=doc_hash,
            full_address="Delivery address could not be verified from the available document."
        )
