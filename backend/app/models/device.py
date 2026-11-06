"""
GeM BidWatch — Device / FCM Token Model
Stores Android device FCM tokens for push notifications.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    fcm_token = Column(String(500), unique=True, nullable=False, index=True)
    device_name = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Device {self.device_name}>"
