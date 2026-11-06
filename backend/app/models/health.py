"""
GeM BidWatch — Health / Monitor Status Model
Tracks each polling job's outcome for the dashboard.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class MonitorHealth(Base):
    __tablename__ = "monitor_health"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, nullable=True)
    profile_name = Column(String(200), nullable=True)
    checked_at = Column(DateTime(timezone=True), server_default=func.now())
    bids_fetched = Column(Integer, default=0)
    bids_new = Column(Integer, default=0)
    bids_matched = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<MonitorHealth profile={self.profile_id} at={self.checked_at}>"
