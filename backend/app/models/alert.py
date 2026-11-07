"""
GeM BidWatch — Alert Database Model
Includes acknowledgement tracking, match reasons, and unique constraint.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)
    bid_id = Column(Integer, ForeignKey("bids.id"), nullable=False, index=True)

    matched_keywords = Column(Text, nullable=True)
    match_reason = Column(Text, nullable=True)
    status = Column(String(50), default="NEW", index=True)  # NEW, UNACKNOWLEDGED, ACKNOWLEDGED
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)

    notification_sent = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime(timezone=True), nullable=True)
    notification_error = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Prevent duplicate alerts for the same profile and bid
    __table_args__ = (
        UniqueConstraint('profile_id', 'bid_id', name='uq_profile_bid'),
    )

    # Relationships for eager loading
    bid = relationship("Bid", backref="alerts", lazy="select")
    profile = relationship("Profile", backref="alerts", lazy="select")

    def __repr__(self):
        return f"<Alert profile={self.profile_id} bid={self.bid_id}>"
