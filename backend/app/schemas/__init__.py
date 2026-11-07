"""
GeM BidWatch — Pydantic Schemas (request/response models)
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ─── BID SCHEMAS ─────────────────────────────────────────────────────────────

class BidBase(BaseModel):
    gem_bid_id: int
    bid_number: str
    bid_number_parent: Optional[str] = None
    category_name: Optional[str] = None
    category_key: Optional[str] = None
    category_mapping_status: Optional[str] = "UNKNOWN"
    quantity: Optional[int] = None
    bid_type: Optional[int] = None
    status: Optional[int] = None
    is_high_value: bool = False
    estimated_value: Optional[float] = None
    ministry_name: Optional[str] = None
    dept_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    original_end_date: Optional[datetime] = None
    revised_end_date: Optional[datetime] = None
    corrigendum_status: Optional[str] = "NONE"
    corrigendum_doc_url: Optional[str] = None
    corrigendum_details: Optional[str] = None
    date_source: Optional[str] = "OFFICIAL_BID_DOCUMENT"
    bid_status: Optional[str] = "ACTIVE"

    # Location Breakdown
    buyer_state: Optional[str] = None
    buyer_district: Optional[str] = None
    buyer_city: Optional[str] = None

    consignee_state: Optional[str] = None
    consignee_district: Optional[str] = None
    consignee_city: Optional[str] = None

    delivery_state: Optional[str] = None
    delivery_district: Optional[str] = None
    delivery_city: Optional[str] = None
    delivery_address: Optional[str] = None

    # PDF Extracted Delivery Location Fields
    pdf_delivery_address: Optional[str] = None
    pdf_delivery_city: Optional[str] = None
    pdf_delivery_district: Optional[str] = None
    pdf_delivery_state: Optional[str] = None
    pdf_delivery_pincode: Optional[str] = None
    pdf_delivery_consignee: Optional[str] = None
    pdf_delivery_org: Optional[str] = None
    pdf_page_number: Optional[int] = None
    pdf_extraction_method: Optional[str] = "PDF_TEXT"
    pdf_confidence_score: Optional[float] = None
    pdf_verification_status: Optional[str] = "UNKNOWN"
    pdf_processed_at: Optional[datetime] = None
    pdf_doc_hash: Optional[str] = None

    raw_location_text: Optional[str] = None
    location_verification_status: Optional[str] = "UNKNOWN"
    target_location_status: Optional[str] = "UNKNOWN"
    data_source_classification: Optional[str] = "LIVE_VERIFIED"

    # Strict Document-to-Bid Synchronization & Provenance Fields
    official_source_url: Optional[str] = None
    original_pdf_url: Optional[str] = None
    original_pdf_checksum: Optional[str] = None
    document_version: Optional[str] = "1.0"
    original_publication_date: Optional[datetime] = None
    latest_revised_deadline: Optional[datetime] = None
    corrigendum_reference: Optional[str] = None
    corrigendum_date: Optional[datetime] = None
    latest_verified_status: Optional[str] = "ACTIVE"
    raw_extracted_text: Optional[str] = None
    extracted_category: Optional[str] = None
    extracted_consignee_name: Optional[str] = None
    extracted_delivery_address: Optional[str] = None
    extracted_city: Optional[str] = None
    extracted_district: Optional[str] = None
    extracted_state: Optional[str] = None
    extracted_pincode: Optional[str] = None
    pdf_bid_number: Optional[str] = None
    pdf_details_page_number: Optional[int] = None
    extraction_timestamp: Optional[datetime] = None
    verification_timestamp: Optional[datetime] = None
    data_confidence: Optional[float] = None
    synchronization_status: Optional[str] = "PENDING"
    verification_reason: Optional[str] = None

    bid_url: Optional[str] = None
    cat_id: Optional[str] = None


class BidCreate(BidBase):
    raw_source_record: Optional[str] = None
    source_retrieval_time: Optional[datetime] = None


class BidOut(BidBase):
    id: int
    first_seen_at: datetime
    published_date: Optional[str] = None
    published_time: Optional[str] = None
    end_date_formatted: Optional[str] = None
    end_time_formatted: Optional[str] = None
    original_end_date_formatted: Optional[str] = None
    original_end_time_formatted: Optional[str] = None
    revised_end_date_formatted: Optional[str] = None
    revised_end_time_formatted: Optional[str] = None
    time_remaining: Optional[str] = None
    display_location: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── PROFILE SCHEMAS ─────────────────────────────────────────────────────────

class ProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    is_active: bool = True
    state: str = Field(..., min_length=1)
    cities: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    ministry_filter: Optional[List[str]] = None
    poll_interval_seconds: int = 300


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    state: Optional[str] = None
    cities: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    ministry_filter: Optional[List[str]] = None
    poll_interval_seconds: Optional[int] = None


class ProfileOut(ProfileCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── ALERT SCHEMAS ───────────────────────────────────────────────────────────

class AlertOut(BaseModel):
    id: int
    profile_id: int
    bid_id: int
    matched_keywords: Optional[str] = None
    match_reason: Optional[str] = None
    status: Optional[str] = "NEW"
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    notification_sent: bool
    notification_sent_at: Optional[datetime] = None
    notification_error: Optional[str] = None
    retry_count: int
    created_at: datetime
    bid: Optional[BidOut] = None

    model_config = {"from_attributes": True}


class AlertCountStats(BaseModel):
    total_alerts: int
    new_alerts: int
    unacknowledged_alerts: int
    acknowledged_alerts: int
    dispatched_notifications: int
    failed_notifications: int


# ─── DEVICE SCHEMAS ──────────────────────────────────────────────────────────

class DeviceRegister(BaseModel):
    fcm_token: str = Field(..., min_length=10)
    device_name: Optional[str] = None


class DeviceOut(BaseModel):
    id: int
    fcm_token: str
    device_name: Optional[str]
    is_active: bool
    registered_at: datetime

    model_config = {"from_attributes": True}


# ─── HEALTH SCHEMAS ──────────────────────────────────────────────────────────

class HealthOut(BaseModel):
    id: int
    profile_id: Optional[int]
    profile_name: Optional[str]
    checked_at: datetime
    bids_fetched: int
    bids_new: int
    bids_matched: int
    success: bool
    error_message: Optional[str]
    duration_seconds: Optional[int]

    model_config = {"from_attributes": True}


class SystemStatus(BaseModel):
    status: str
    monitor_running: bool
    total_profiles: int
    active_profiles: int
    total_bids_in_db: int
    active_bids_in_db: int
    expired_bids_in_db: int
    total_alerts: int
    unacknowledged_alerts: int
    last_check: Optional[datetime]
