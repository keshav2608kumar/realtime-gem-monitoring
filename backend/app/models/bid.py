"""
GeM BidWatch — Bid Database Model
Includes comprehensive location segregation, provenance tracking, and status lifecycle.
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
    category_key = Column(String(100), index=True, nullable=True)  # Canonical category ID (e.g. TONER_INK_PRINTER_CONSUMABLES)
    category_mapping_status = Column(String(50), default="UNKNOWN")  # VERIFIED, MAPPED, UNMAPPED, UNKNOWN
    quantity = Column(Integer, nullable=True)
    bid_type = Column(Integer, nullable=True)   # 1=BID, 2=RA, 5=DirectRA
    status = Column(Integer, nullable=True)
    is_high_value = Column(Boolean, default=False)
    estimated_value = Column(Float, nullable=True)

    ministry_name = Column(String(255), nullable=True)
    dept_name = Column(String(255), nullable=True)

    # Dates
    start_date = Column(DateTime(timezone=True), nullable=True)  # Published date
    end_date = Column(DateTime(timezone=True), nullable=True)    # Bid deadline / closing date
    bid_status = Column(String(50), default="ACTIVE", index=True)  # ACTIVE, CLOSING_SOON, EXPIRING_TODAY, EXPIRED, etc.

    # Segregated Location Fields
    buyer_state = Column(String(100), nullable=True)
    buyer_district = Column(String(100), nullable=True)
    buyer_city = Column(String(100), nullable=True)

    consignee_state = Column(String(100), nullable=True)
    consignee_district = Column(String(100), nullable=True)
    consignee_city = Column(String(100), nullable=True)

    delivery_state = Column(String(100), nullable=True)
    delivery_district = Column(String(100), nullable=True)
    delivery_city = Column(String(100), nullable=True)
    delivery_address = Column(Text, nullable=True)

    # PDF Document Extracted Delivery Location Fields
    pdf_delivery_address = Column(Text, nullable=True)
    pdf_delivery_city = Column(String(100), nullable=True)
    pdf_delivery_district = Column(String(100), nullable=True)
    pdf_delivery_state = Column(String(100), nullable=True)
    pdf_delivery_pincode = Column(String(20), nullable=True)
    pdf_delivery_consignee = Column(String(200), nullable=True)
    pdf_delivery_org = Column(String(255), nullable=True)
    pdf_page_number = Column(Integer, nullable=True)
    pdf_extraction_method = Column(String(50), default="PDF_TEXT")  # PDF_TEXT, OCR
    pdf_confidence_score = Column(Float, nullable=True)
    pdf_verification_status = Column(String(50), default="UNKNOWN")  # VERIFIED, PARTIALLY_VERIFIED, AMBIGUOUS, UNKNOWN, PDF_UNAVAILABLE
    pdf_processed_at = Column(DateTime(timezone=True), nullable=True)
    pdf_doc_hash = Column(String(64), nullable=True)

    raw_location_text = Column(Text, nullable=True)
    location_verification_status = Column(String(50), default="UNKNOWN")  # VERIFIED, NORMALIZED, AMBIGUOUS, UNKNOWN

    # Data Provenance & Classification
    data_source_classification = Column(String(50), default="LIVE_VERIFIED")  # LIVE_VERIFIED, IMPORTED, SIMULATED
    raw_source_record = Column(Text, nullable=True)
    source_retrieval_time = Column(DateTime(timezone=True), nullable=True)
    data_ingestion_time = Column(DateTime(timezone=True), server_default=func.now())

    bid_url = Column(String(500), nullable=True)  # link to official GeM document
    cat_id = Column(String(200), nullable=True)

    # Internal tracking
    first_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Bid {self.bid_number}>"
