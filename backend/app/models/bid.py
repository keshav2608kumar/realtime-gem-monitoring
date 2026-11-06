"""
GeM BidWatch — Bid Database Model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text
from sqlalchemy.sql import func
from app.database import Base


class Bid(Base):
    __tablename__ = "bids"

    id = Column(Integer, primary_key=True, index=True)
    gem_bid_id = Column(Integer, unique=True, index=True, nullable=False)  # b_id from GeM
    bid_number = Column(String(100), unique=True, index=True, nullable=False)  # e.g. GEM/2026/B/...
    bid_number_parent = Column(String(100), nullable=True)
    category_name = Column(Text, nullable=True)
    quantity = Column(Integer, nullable=True)
    bid_type = Column(Integer, nullable=True)   # 1=BID, 2=RA, 5=DirectRA
    status = Column(Integer, nullable=True)
    is_high_value = Column(Boolean, default=False)

    ministry_name = Column(String(255), nullable=True)
    dept_name = Column(String(255), nullable=True)

    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)

    # Geographic info (from search context)
    consignee_state = Column(String(100), nullable=True)
    consignee_city = Column(String(100), nullable=True)

    bid_url = Column(String(500), nullable=True)  # link to PDF
    cat_id = Column(String(200), nullable=True)

    # Internal tracking
    first_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Bid {self.bid_number}>"
