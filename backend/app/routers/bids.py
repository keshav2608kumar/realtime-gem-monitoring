"""
Bids Router — Read-only access to discovered bids
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional

from app.database import get_db
from app.models import Bid
from app.schemas import BidOut, BidCreate

router = APIRouter(prefix="/bids", tags=["Bids"])


@router.get("/", response_model=List[BidOut])
def list_bids(
    skip: int = 0,
    limit: int = Query(default=20, le=100),
    state: Optional[str] = None,
    city: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Bid).order_by(desc(Bid.first_seen_at))
    if state:
        q = q.filter(Bid.consignee_state.ilike(f"%{state}%"))
    if city:
        q = q.filter(Bid.consignee_city.ilike(f"%{city}%"))
    if keyword:
        q = q.filter(Bid.category_name.ilike(f"%{keyword}%"))
    return q.offset(skip).limit(limit).all()


@router.post("/batch-sync", status_code=201)
def batch_sync_bids(bids: List[BidCreate], db: Session = Depends(get_db)):
    """
    Ingest a batch of newly fetched bids from an Indian scanner node.
    Deduplicates by gem_bid_id, checks active profiles, and generates alerts.
    """
    from app.models import Profile, Alert
    from app.gem.filter_matcher import match_bid_to_profile, keywords_summary
    from app.schemas import ProfileOut

    profiles = db.query(Profile).filter(Profile.is_active == True).all()
    inserted_count = 0
    alerts_created = 0

    for bid_data in bids:
        existing = db.query(Bid).filter(Bid.gem_bid_id == bid_data.gem_bid_id).first()
        if existing:
            db_bid = existing
        else:
            db_bid = Bid(**bid_data.model_dump())
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
                        notification_sent=False,
                    )
                    db.add(new_alert)
                    alerts_created += 1

    db.commit()
    return {
        "status": "success",
        "bids_received": len(bids),
        "bids_inserted": inserted_count,
        "alerts_created": alerts_created,
    }


@router.get("/{bid_id}", response_model=BidOut)
def get_bid(bid_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    b = db.query(Bid).filter(Bid.id == bid_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Bid not found")
    return b
