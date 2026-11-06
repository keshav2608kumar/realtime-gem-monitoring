"""
Bids Router — Read-only access to discovered bids
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional

from app.database import get_db
from app.models import Bid
from app.schemas import BidOut

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


@router.get("/{bid_id}", response_model=BidOut)
def get_bid(bid_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    b = db.query(Bid).filter(Bid.id == bid_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Bid not found")
    return b
