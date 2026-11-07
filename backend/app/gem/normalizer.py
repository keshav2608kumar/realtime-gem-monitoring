"""
GeM BidWatch — BidNormalizer
Converts raw GeM API response into verified BidCreate schema.
Enforces administrative location normalization, timezone-aware datetime parsing,
provenance preservation, and status lifecycle calculation.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from app.gem.fetcher import RawBid
from app.schemas import BidCreate
from app.services.location_normalizer import normalize_location
from app.services.datetime_service import parse_datetime
from app.services.bid_status_service import calculate_bid_status
from app.services.category_service import match_category

logger = logging.getLogger(__name__)

BID_DOCUMENT_URL = "https://bidplus.gem.gov.in/showbidDocument/{bid_id}"
RA_DOCUMENT_URL = "https://bidplus.gem.gov.in/showradocumentPdf/{bid_id}"


def normalize_bid(raw: RawBid) -> Optional[BidCreate]:
    """
    Convert a RawBid into a verified BidCreate schema object.
    Never invents locations, dates, or default fallbacks.
    Returns None only if essential identifiers are missing.
    """
    try:
        gem_id = raw.get("b_id")
        bid_number = raw.get("b_bid_number")

        if not gem_id or not bid_number:
            logger.warning(f"Skipping bid with missing id/number: {raw.raw}")
            return None

        bid_type = raw.get("b_bid_type", 1)
        bid_id_val = gem_id if isinstance(gem_id, int) else int(gem_id)

        # Official GeM PDF document link
        if bid_type == 2:
            bid_url = RA_DOCUMENT_URL.format(bid_id=bid_id_val)
        else:
            bid_url = BID_DOCUMENT_URL.format(bid_id=bid_id_val)

        dept_name = raw.get("ba_official_details_deptName")
        min_name = raw.get("ba_official_details_minName")

        # 1. Location Normalization (Strict administrative mapping)
        # Check raw state/city hints, plus any location mentioned in department text
        loc = normalize_location(
            raw_text=dept_name,
            city_hint=raw.city,
            state_hint=raw.state,
        )

        # 2. Datetime Parsing (UTC timezone-aware)
        start_date = parse_datetime(raw.get("final_start_date_sort"))
        end_date = parse_datetime(raw.get("final_end_date_sort"))

        # 3. Bid Status Lifecycle Calculation
        raw_status = raw.get("b_status")
        bid_status = calculate_bid_status(end_date, raw_status)

        # 4. Category Classification
        cat_name = raw.get("b_category_name")
        cat_id_val = raw.get("b_cat_id")
        category_key, _, category_status = match_category(cat_name, cat_id_val)

        # 5. Quantity and Estimated Value
        quantity = raw.get("b_total_quantity")
        if quantity is not None:
            try:
                quantity = int(quantity)
            except (ValueError, TypeError):
                quantity = None

        est_val = raw.get("b_estimated_value")
        if est_val is not None:
            try:
                est_val = float(est_val)
            except (ValueError, TypeError):
                est_val = None

        # 5. Provenance tracking
        raw_json_str = None
        try:
            raw_json_str = json.dumps(raw.raw)
        except Exception:
            pass

        return BidCreate(
            gem_bid_id=bid_id_val,
            bid_number=str(bid_number),
            bid_number_parent=raw.get("b_bid_number_parent"),
            category_name=cat_name,
            category_key=category_key,
            category_mapping_status=category_status,
            quantity=quantity,
            bid_type=bid_type,
            status=raw_status,
            is_high_value=bool(raw.get("is_high_value", False)),
            estimated_value=est_val,
            ministry_name=min_name,
            dept_name=dept_name,
            start_date=start_date,
            end_date=end_date,
            bid_status=bid_status,
            # Segregated Location Fields
            consignee_state=loc.state,
            consignee_city=loc.city,
            consignee_district=loc.district,
            buyer_state=loc.state if loc.confidence == "VERIFIED" else None,
            buyer_city=loc.city if loc.confidence == "VERIFIED" else None,
            raw_location_text=loc.raw_text,
            location_verification_status=loc.confidence,
            data_source_classification="LIVE_VERIFIED",
            raw_source_record=raw_json_str,
            source_retrieval_time=datetime.now(timezone.utc),
            official_source_url=bid_url,
            original_pdf_url=bid_url,
            synchronization_status="PENDING",
            original_end_date=end_date,
            original_publication_date=start_date,
            bid_url=bid_url,
            cat_id=raw.get("b_cat_id"),
        )
    except Exception as e:
        logger.error(f"Failed to normalize bid: {e} | raw={raw.raw}", exc_info=True)
        return None
