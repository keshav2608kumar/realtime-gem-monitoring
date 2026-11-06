"""
GeM BidWatch — BidNormalizer
Converts raw GeM API response into clean BidCreate schema.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from app.gem.fetcher import RawBid
from app.schemas import BidCreate

logger = logging.getLogger(__name__)

BID_DOCUMENT_URL = "https://bidplus.gem.gov.in/showbidDocument/{bid_id}"
RA_DOCUMENT_URL = "https://bidplus.gem.gov.in/showradocumentPdf/{bid_id}"


def parse_gem_datetime(date_str: Optional[str]) -> Optional[datetime]:
    """Parse GeM ISO datetime string like '2026-11-07T16:00:00Z'."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def normalize_bid(raw: RawBid) -> Optional[BidCreate]:
    """
    Convert a RawBid into a BidCreate schema object.
    Returns None if essential fields are missing.
    """
    try:
        gem_id = raw.get("b_id")
        bid_number = raw.get("b_bid_number")

        if not gem_id or not bid_number:
            logger.warning(f"Skipping bid with missing id/number: {raw.raw}")
            return None

        bid_type = raw.get("b_bid_type", 1)
        bid_id_val = gem_id if isinstance(gem_id, int) else int(gem_id)

        # Choose correct document URL based on bid type
        if bid_type == 2:
            bid_url = RA_DOCUMENT_URL.format(bid_id=bid_id_val)
        else:
            bid_url = BID_DOCUMENT_URL.format(bid_id=bid_id_val)

        return BidCreate(
            gem_bid_id=bid_id_val,
            bid_number=str(bid_number),
            bid_number_parent=raw.get("b_bid_number_parent"),
            category_name=raw.get("b_category_name"),
            quantity=raw.get("b_total_quantity"),
            bid_type=bid_type,
            status=raw.get("b_status"),
            is_high_value=bool(raw.get("is_high_value", False)),
            ministry_name=raw.get("ba_official_details_minName"),
            dept_name=raw.get("ba_official_details_deptName"),
            start_date=parse_gem_datetime(raw.get("final_start_date_sort")),
            end_date=parse_gem_datetime(raw.get("final_end_date_sort")),
            consignee_state=raw.state,
            consignee_city=raw.city,
            bid_url=bid_url,
            cat_id=raw.get("b_cat_id"),
        )
    except Exception as e:
        logger.error(f"Failed to normalize bid: {e} | raw={raw.raw}")
        return None
