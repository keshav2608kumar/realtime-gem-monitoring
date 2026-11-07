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
from app.services.location_normalizer import normalize_location

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

    out = BidOut(
        id=b.id,
        gem_bid_id=b.gem_bid_id,
        bid_number=b.bid_number,
        bid_number_parent=b.bid_number_parent,
        category_name=b.category_name,
        quantity=b.quantity,
        bid_type=b.bid_type,
        status=b.status,
        is_high_value=b.is_high_value or False,
        estimated_value=b.estimated_value,
        ministry_name=b.ministry_name,
        dept_name=b.dept_name,
        start_date=b.start_date,
        end_date=b.end_date,
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
        raw_location_text=b.raw_location_text or loc.raw_text,
        location_verification_status=b.location_verification_status or loc.confidence,
        data_source_classification=b.data_source_classification or "LIVE_VERIFIED",
        bid_url=b.bid_url,
        cat_id=b.cat_id,
        first_seen_at=b.first_seen_at or now,
        published_date=format_ist_date(b.start_date),
        published_time=format_ist_time(b.start_date),
        end_date_formatted=format_ist_date(b.end_date),
        end_time_formatted=format_ist_time(b.end_date),
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
    keyword: Optional[str] = None,
    category: Optional[str] = None,
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

    # 2. Location Filters
    if state:
        q = q.filter(
            or_(
                Bid.consignee_state.ilike(f"%{state}%"),
                Bid.buyer_state.ilike(f"%{state}%")
            )
        )
    if city:
        q = q.filter(
            or_(
                Bid.consignee_city.ilike(f"%{city}%"),
                Bid.buyer_city.ilike(f"%{city}%")
            )
        )

    # 3. Keyword / Category / Dept Filters
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
    return {
        "total_bids": total,
        "active_bids": active,
        "expired_bids": expired,
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


@router.get("/{bid_id}", response_model=BidOut)
def get_bid(bid_id: int, db: Session = Depends(get_db)):
    b = db.query(Bid).filter(Bid.id == bid_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Bid not found")
    return _enrich_bid(b)
