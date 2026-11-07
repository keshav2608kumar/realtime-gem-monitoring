"""
GeM BidWatch — Monitoring Profile Model
A profile defines what to watch: location + category keywords + value range.
"""
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)       # e.g. "Bangalore Toner"
    is_active = Column(Boolean, default=True)

    # Location filters (matches GeM city name variants)
    state = Column(String(100), nullable=False)       # e.g. "KARNATAKA"
    # JSON list of city variants to monitor simultaneously
    cities = Column(JSON, nullable=True)              # ["BANGALORE","Bangalore Urban","BENGALURU URBAN","Bengaluru"]

    # Category/keyword filters
    keywords = Column(JSON, nullable=True)            # ["toner","cartridge","printer","ink"]
    categories = Column(JSON, nullable=True)          # ["TONER_INK_PRINTER_CONSUMABLES", "COMPUTER_PRINTER_V2"]

    # Value filters
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)

    # Ministry filter
    ministry_filter = Column(JSON, nullable=True)     # e.g. ["Ministry of Defence"] or null for all

    # Polling config
    poll_interval_seconds = Column(Integer, default=300)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Profile {self.name}>"
