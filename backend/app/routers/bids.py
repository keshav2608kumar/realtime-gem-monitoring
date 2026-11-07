"""
Bids Router — Advanced querying, multi-mode sorting, filtering & batch ingestion
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_, and_
from typing import List, Optional
from datetime import datetime, timezone

from app.database import get_db
from app.models import Bid, Profile, Alert
from app.schemas import BidOut, BidCreate
from app.services.datetime_service import (
    format_ist_date, format_ist_time, compute_time_remaining, to_ist, UTC_TZ
)
from app.services.bid_status_service import (
    calculate_bid_status, is_active_status, STATUS_ACTIVE, STATUS_EXPIRED, STATUS_CLOSING_SOON
)
from app.services.location_normalizer import (
    normalize_location, resolve_effective_bid_delivery_location,
    STATUS_VERIFIED_BENGALURU_URBAN, STATUS_PARTIALLY_VERIFIED,
    STATUS_AMBIGUOUS, STATUS_OUTSIDE_TARGET, STATUS_UNKNOWN
)
from app.services.category_service import match_category, get_all_target_categories, CATEGORIES_BY_ID
from app.services.pdf_location_extractor import extract_location_from_pdf

router = APIRouter(prefix="/bids", tags=["Bids"])


def _enrich_bid(b: Bid, now_utc: Optional[datetime] = None) -> BidOut:
    """Enrich a DB Bid model with formatted IST dates, time remaining, and status."""
    now = now_utc or datetime.now(UTC_TZ)

    # Recalculate dynamic status based on verified end_date
    current_status = calculate_bid_status(b.end_date, b.status, now_utc=now)
    time_rem = compute_time_remaining(b.end_date, now_utc=now)

    # Build display location
    loc = normalize_location(
        raw_text=b.dept_name,
        city_hint=b.consignee_city or b.buyer_city,
        state_hint=b.consignee_state or b.buyer_state,
    )

    # Resolve target location status if missing
    t_status = getattr(b, "target_location_status", None)
    if not t_status or t_status == "UNKNOWN":
        t_status, _, _, _, _ = resolve_effective_bid_delivery_location(b)

    # Resolve category key if missing
    cat_key = b.category_key
    cat_status = b.category_mapping_status or "UNKNOWN"
    if not cat_key and b.category_name:
        resolved_key, _, resolved_status = match_category(b.category_name, b.cat_id)
        if resolved_key:
            cat_key = resolved_key
            cat_status = resolved_status

    out = BidOut(
        id=b.id,
        gem_bid_id=b.gem_bid_id,
        bid_number=b.bid_number,
        bid_number_parent=b.bid_number_parent,
        category_name=b.category_name,
        category_key=cat_key,
        category_mapping_status=cat_status,
        quantity=b.quantity,
        bid_type=b.bid_type,
        status=b.status,
        is_high_value=b.is_high_value or False,
        estimated_value=b.estimated_value,
        ministry_name=b.ministry_name,
        dept_name=b.dept_name,
        start_date=b.start_date,
        end_date=b.end_date,
        original_end_date=b.original_end_date,
        revised_end_date=b.revised_end_date,
        corrigendum_status=b.corrigendum_status or "NONE",
        corrigendum_doc_url=b.corrigendum_doc_url,
        corrigendum_details=b.corrigendum_details,
        date_source=b.date_source or "OFFICIAL_BID_DOCUMENT",
        bid_status=current_status,
        buyer_state=b.buyer_state,
        buyer_district=b.buyer_district,
        buyer_city=b.buyer_city,
        consignee_state=b.consignee_state or loc.state,
        consignee_district=b.consignee_district or loc.district,
        consignee_city=b.consignee_city or loc.city,
        delivery_state=b.delivery_state,
        delivery_district=b.delivery_district,
        delivery_city=b.delivery_city,
        delivery_address=b.delivery_address,
        # PDF Extracted Delivery Location
        pdf_delivery_address=b.pdf_delivery_address,
        pdf_delivery_city=b.pdf_delivery_city,
        pdf_delivery_district=b.pdf_delivery_district,
        pdf_delivery_state=b.pdf_delivery_state,
        pdf_delivery_pincode=b.pdf_delivery_pincode,
        pdf_delivery_consignee=b.pdf_delivery_consignee,
        pdf_delivery_org=b.pdf_delivery_org,
        pdf_page_number=b.pdf_page_number,
        pdf_extraction_method=b.pdf_extraction_method or "PDF_TEXT",
        pdf_confidence_score=b.pdf_confidence_score,
        pdf_verification_status=b.pdf_verification_status or "UNKNOWN",
        pdf_processed_at=b.pdf_processed_at,
        pdf_doc_hash=b.pdf_doc_hash,
        raw_location_text=b.raw_location_text or loc.raw_text,
        location_verification_status=b.location_verification_status or loc.confidence,
        target_location_status=t_status or "UNKNOWN",
        data_source_classification=b.data_source_classification or "LIVE_VERIFIED",
        bid_url=b.bid_url,
        cat_id=b.cat_id,
        first_seen_at=b.first_seen_at or now,
        published_date=format_ist_date(b.start_date),
        published_time=format_ist_time(b.start_date),
        end_date_formatted=format_ist_date(b.end_date),
        end_time_formatted=format_ist_time(b.end_date),
        original_end_date_formatted=format_ist_date(b.original_end_date) if b.original_end_date else None,
        original_end_time_formatted=format_ist_time(b.original_end_date) if b.original_end_date else None,
        revised_end_date_formatted=format_ist_date(b.revised_end_date) if b.revised_end_date else None,
        revised_end_time_formatted=format_ist_time(b.revised_end_date) if b.revised_end_date else None,
        time_remaining=time_rem["human"],
        display_location=loc.display_location,
    )
    return out


@router.get("/", response_model=List[BidOut])
def list_bids(
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    status: str = Query(
        default="active",
        description="Filter by lifecycle status: 'active' (default), 'all', 'expired', 'closing_soon', 'cancelled'"
    ),
    sort_by: str = Query(
        default="closing_soonest",
        description=(
            "Sort order: 'latest_published', 'oldest_published', 'closing_soonest', "
            "'closing_latest', 'newly_added', 'recently_updated', 'highest_value', 'lowest_value'"
        )
    ),
    state: Optional[str] = None,
    city: Optional[str] = None,
    location_type: str = Query(
        default="consignee",
        description="Location field to match: 'consignee' (default), 'buyer', 'delivery', 'pdf_delivery', 'any'"
    ),
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    categories: Optional[List[str]] = Query(
        default=None,
        description="One or more canonical product category IDs (e.g. TONER_INK_PRINTER_CONSUMABLES, SCANNER_V3)"
    ),
    scope: Optional[str] = Query(
        default=None,
        description="Target location scope: 'bengaluru_urban' (verified matching feed), 'review', 'outside', 'all'"
    ),
    target_status: Optional[str] = Query(
        default=None,
        description="Filter by exact target_location_status (e.g. VERIFIED_BENGALURU_URBAN, PARTIALLY_VERIFIED, AMBIGUOUS, OUTSIDE_TARGET, UNKNOWN)"
    ),
    dept: Optional[str] = None,
    source_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    List bids with professional server-side sorting, status segregation, and location filters.
    By default, EXPIRED bids are excluded from the active feed.
    """
    now = datetime.now(UTC_TZ)
    q = db.query(Bid)

    # 1. Lifecycle status filter
    status_lower = status.lower().strip()
    if status_lower == "active":
        # Only active, closing soon, and expiring today (end_date in future or null)
        q = q.filter(or_(Bid.end_date == None, Bid.end_date > now))
    elif status_lower == "expired":
        q = q.filter(and_(Bid.end_date != None, Bid.end_date <= now))
    elif status_lower == "closing_soon":
        from datetime import timedelta
        soon = now + timedelta(hours=24)
        q = q.filter(and_(Bid.end_date > now, Bid.end_date <= soon))
    elif status_lower == "cancelled":
        q = q.filter(Bid.status == 2)
    # 'all' applies no status filtering

    # 2. Location Filters (Segregated by location_type)
    loc_type = (location_type or "consignee").lower().strip()
    if state:
        if loc_type == "buyer":
            q = q.filter(Bid.buyer_state.ilike(f"%{state}%"))
        elif loc_type == "delivery":
            q = q.filter(Bid.delivery_state.ilike(f"%{state}%"))
        elif loc_type == "pdf_delivery":
            q = q.filter(Bid.pdf_delivery_state.ilike(f"%{state}%"))
        elif loc_type == "any":
            q = q.filter(
                or_(
                    Bid.consignee_state.ilike(f"%{state}%"),
                    Bid.buyer_state.ilike(f"%{state}%"),
                    Bid.delivery_state.ilike(f"%{state}%"),
                    Bid.pdf_delivery_state.ilike(f"%{state}%"),
                )
            )
        else:  # default "consignee"
            q = q.filter(
                or_(
                    Bid.consignee_state.ilike(f"%{state}%"),
                    Bid.buyer_state.ilike(f"%{state}%")
                )
            )

    if city:
        if loc_type == "buyer":
            q = q.filter(Bid.buyer_city.ilike(f"%{city}%"))
        elif loc_type == "delivery":
            q = q.filter(Bid.delivery_city.ilike(f"%{city}%"))
        elif loc_type == "pdf_delivery":
            q = q.filter(Bid.pdf_delivery_city.ilike(f"%{city}%"))
        elif loc_type == "any":
            q = q.filter(
                or_(
                    Bid.consignee_city.ilike(f"%{city}%"),
                    Bid.buyer_city.ilike(f"%{city}%"),
                    Bid.delivery_city.ilike(f"%{city}%"),
                    Bid.pdf_delivery_city.ilike(f"%{city}%"),
                )
            )
        else:  # default "consignee"
            q = q.filter(
                or_(
                    Bid.consignee_city.ilike(f"%{city}%"),
                    Bid.buyer_city.ilike(f"%{city}%")
                )
            )

    # 3. Canonical Product Category Filters
    if categories:
        selected_cat_keys = set()
        for item in categories:
            if not item:
                continue
            for part in str(item).split(","):
                part_clean = part.strip().upper()
                if part_clean in CATEGORIES_BY_ID:
                    selected_cat_keys.add(part_clean)
                else:
                    k, _, _ = match_category(part)
                    if k:
                        selected_cat_keys.add(k)

        if selected_cat_keys:
            cat_filters = [Bid.category_key.in_(list(selected_cat_keys))]
            for ck in selected_cat_keys:
                c_def = CATEGORIES_BY_ID.get(ck)
                if c_def:
                    cat_filters.append(Bid.category_name.ilike(f"%{c_def.display_name}%"))
            q = q.filter(or_(*cat_filters))

    # 4. Target Location Scope Filter
    if target_status:
        q = q.filter(Bid.target_location_status == target_status.strip().upper())
    elif scope:
        scope_clean = scope.lower().strip()
        if scope_clean in ("bengaluru_urban", "bangalore_urban", "verified", "target", "matching"):
            q = q.filter(Bid.target_location_status == STATUS_VERIFIED_BENGALURU_URBAN)
        elif scope_clean in ("review", "partially_verified", "ambiguous", "unverified"):
            q = q.filter(Bid.target_location_status.in_([STATUS_PARTIALLY_VERIFIED, STATUS_AMBIGUOUS, STATUS_UNKNOWN]))
        elif scope_clean in ("outside", "outside_target"):
            q = q.filter(Bid.target_location_status == STATUS_OUTSIDE_TARGET)

    # 5. Keyword / Legacy Category / Dept Filters
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(
            or_(
                Bid.category_name.ilike(kw),
                Bid.bid_number.ilike(kw),
                Bid.dept_name.ilike(kw),
                Bid.ministry_name.ilike(kw),
            )
        )
    if category:
        q = q.filter(Bid.category_name.ilike(f"%{category}%"))
    if dept:
        q = q.filter(Bid.dept_name.ilike(f"%{dept}%"))
    if source_type:
        q = q.filter(Bid.data_source_classification == source_type.upper())

    # 4. Sorting Modes
    sort_mode = sort_by.lower().strip()
    if sort_mode == "latest_published":
        q = q.order_by(Bid.start_date.desc().nullslast())
    elif sort_mode == "oldest_published":
        q = q.order_by(Bid.start_date.asc().nullslast())
    elif sort_mode == "closing_soonest":
        q = q.order_by(Bid.end_date.asc().nullslast())
    elif sort_mode == "closing_latest":
        q = q.order_by(Bid.end_date.desc().nullslast())
    elif sort_mode == "newly_added":
        q = q.order_by(Bid.first_seen_at.desc())
    elif sort_mode == "recently_updated":
        q = q.order_by(Bid.updated_at.desc().nullslast())
    elif sort_mode == "highest_value":
        q = q.order_by(Bid.estimated_value.desc().nullslast())
    elif sort_mode == "lowest_value":
        q = q.order_by(Bid.estimated_value.asc().nullslast())
    else:
        q = q.order_by(Bid.end_date.asc().nullslast())

    raw_list = q.offset(skip).limit(limit).all()
    return [_enrich_bid(b, now_utc=now) for b in raw_list]


@router.get("/summary/stats")
def get_bids_summary_stats(db: Session = Depends(get_db)):
    """Return verified count aggregates for bids."""
    now = datetime.now(UTC_TZ)
    total = db.query(Bid).count()
    active = db.query(Bid).filter(or_(Bid.end_date == None, Bid.end_date > now)).count()
    expired = db.query(Bid).filter(and_(Bid.end_date != None, Bid.end_date <= now)).count()
    bengaluru_urban_verified = db.query(Bid).filter(
        Bid.target_location_status == STATUS_VERIFIED_BENGALURU_URBAN,
        or_(Bid.end_date == None, Bid.end_date > now)
    ).count()
    review_count = db.query(Bid).filter(
        Bid.target_location_status.in_([STATUS_PARTIALLY_VERIFIED, STATUS_AMBIGUOUS, STATUS_UNKNOWN]),
        or_(Bid.end_date == None, Bid.end_date > now)
    ).count()
    outside_target_count = db.query(Bid).filter(
        Bid.target_location_status == STATUS_OUTSIDE_TARGET,
        or_(Bid.end_date == None, Bid.end_date > now)
    ).count()
    return {
        "total_bids": total,
        "active_bids": active,
        "expired_bids": expired,
        "bengaluru_urban_verified": bengaluru_urban_verified,
        "review_count": review_count,
        "outside_target_count": outside_target_count,
        "timestamp_utc": now.isoformat(),
    }


@router.post("/batch-sync", status_code=201)
def batch_sync_bids(bids: List[BidCreate], db: Session = Depends(get_db)):
    """
    Ingest a batch of newly fetched bids from an Indian scanner node.
    Enforces normalized locations, calculates lifecycle status, deduplicates, and generates alerts.
    """
    from app.gem.filter_matcher import match_bid_to_profile, keywords_summary
    from app.schemas import ProfileOut

    profiles = db.query(Profile).filter(Profile.is_active == True).all()
    inserted_count = 0
    updated_count = 0
    alerts_created = 0
    seen_in_batch = set()

    for bid_data in bids:
        if bid_data.gem_bid_id in seen_in_batch:
            continue
        seen_in_batch.add(bid_data.gem_bid_id)

        # Normalize location
        loc = normalize_location(
            raw_text=bid_data.dept_name,
            city_hint=bid_data.consignee_city,
            state_hint=bid_data.consignee_state,
        )

        # Classify target delivery location status
        loc_st, _, _, _, _ = resolve_effective_bid_delivery_location(bid_data)

        # Classify product category
        ckey, _, cstatus = match_category(bid_data.category_name, bid_data.cat_id)

        existing = db.query(Bid).filter(
            (Bid.bid_number == bid_data.bid_number) | (Bid.gem_bid_id == bid_data.gem_bid_id)
        ).first()

        if existing:
            db_bid = existing
            if bid_data.end_date:
                existing.end_date = bid_data.end_date
            if bid_data.start_date:
                existing.start_date = bid_data.start_date
            if bid_data.category_name:
                existing.category_name = bid_data.category_name
            if ckey:
                existing.category_key = ckey
                existing.category_mapping_status = cstatus
            if bid_data.dept_name:
                existing.dept_name = bid_data.dept_name
            if bid_data.ministry_name:
                existing.ministry_name = bid_data.ministry_name
            if loc.city:
                existing.consignee_city = loc.city
            if loc.state:
                existing.consignee_state = loc.state
            if loc.district:
                existing.consignee_district = loc.district
            existing.location_verification_status = loc.confidence
            existing.target_location_status = loc_st
            if bid_data.bid_url:
                existing.bid_url = bid_data.bid_url
            if bid_data.bid_status:
                existing.bid_status = bid_data.bid_status
            updated_count += 1
        else:
            dump = bid_data.model_dump()
            dump["consignee_city"] = loc.city
            dump["consignee_state"] = loc.state
            dump["consignee_district"] = loc.district
            dump["location_verification_status"] = loc.confidence
            dump["target_location_status"] = loc_st
            dump["category_key"] = ckey
            dump["category_mapping_status"] = cstatus
            db_bid = Bid(**dump)
            db.add(db_bid)
            db.flush()
            inserted_count += 1

        for prof in profiles:
            p_out = ProfileOut(
                id=prof.id,
                name=prof.name,
                is_active=prof.is_active,
                state=prof.state,
                cities=prof.cities,
                keywords=prof.keywords,
                min_value=prof.min_value,
                max_value=prof.max_value,
                ministry_filter=prof.ministry_filter,
                poll_interval_seconds=prof.poll_interval_seconds,
                created_at=prof.created_at,
            )
            match = match_bid_to_profile(bid_data, p_out)
            if match.matched:
                already_alerted = db.query(Alert).filter(
                    Alert.profile_id == prof.id,
                    Alert.bid_id == db_bid.id,
                ).first()
                if not already_alerted:
                    new_alert = Alert(
                        profile_id=prof.id,
                        bid_id=db_bid.id,
                        matched_keywords=keywords_summary(match.matched_keywords),
                        match_reason=match.match_reason,
                        status="NEW",
                        acknowledged=False,
                        notification_sent=False,
                    )
                    db.add(new_alert)
                    alerts_created += 1

    db.commit()
    return {
        "status": "success",
        "bids_received": len(bids),
        "bids_inserted": inserted_count,
        "bids_updated": updated_count,
        "alerts_created": alerts_created,
    }


@router.get("/categories/list")
@router.get("/categories")
def list_target_categories():
    """Return the 7 official GeM target categories with stable IDs and exact display names."""
    cats = get_all_target_categories()
    return [
        {
            "id": c.id,
            "display_name": c.display_name,
            "short_code": c.short_code,
            "description": c.description,
        }
        for c in cats
    ]


@router.post("/{bid_id}/extract-pdf", response_model=BidOut)
def trigger_pdf_extraction(bid_id: int, db: Session = Depends(get_db)):
    """
    Extract delivery/consignee address from the final pages of the official GeM Bid PDF.
    Updates database record with structured address, PIN code, and verification status.
    """
    b = db.query(Bid).filter(Bid.id == bid_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Bid not found")

    if not b.bid_url:
        raise HTTPException(status_code=400, detail="No official PDF URL available for this bid")

    res = extract_location_from_pdf(pdf_url=b.bid_url)
    b.pdf_delivery_address = res.full_address
    b.pdf_delivery_city = res.city
    b.pdf_delivery_district = res.district
    b.pdf_delivery_state = res.state
    b.pdf_delivery_pincode = res.pincode
    b.pdf_delivery_consignee = res.consignee_name
    b.pdf_delivery_org = res.organization
    b.pdf_page_number = res.page_number
    b.pdf_extraction_method = res.extraction_method
    b.pdf_confidence_score = res.confidence_score
    b.pdf_verification_status = res.verification_status
    b.pdf_processed_at = datetime.now(timezone.utc)
    b.pdf_doc_hash = res.doc_hash

    # Re-evaluate target location status with newly extracted PDF delivery details
    new_status, _, _, _, _ = resolve_effective_bid_delivery_location(b)
    b.target_location_status = new_status

    db.commit()
    db.refresh(b)
    return _enrich_bid(b)


@router.get("/{bid_id}", response_model=BidOut)
def get_bid(bid_id: int, db: Session = Depends(get_db)):
    b = db.query(Bid).filter(Bid.id == bid_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Bid not found")
    return _enrich_bid(b)
