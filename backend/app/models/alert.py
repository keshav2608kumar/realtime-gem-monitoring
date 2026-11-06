# Add relationships to Alert model for joinedload
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)
    bid_id = Column(Integer, ForeignKey("bids.id"), nullable=False, index=True)

    matched_keywords = Column(Text, nullable=True)
    notification_sent = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime(timezone=True), nullable=True)
    notification_error = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships for eager loading
    bid = relationship("Bid", backref="alerts", lazy="select")
    profile = relationship("Profile", backref="alerts", lazy="select")

    def __repr__(self):
        return f"<Alert profile={self.profile_id} bid={self.bid_id}>"
