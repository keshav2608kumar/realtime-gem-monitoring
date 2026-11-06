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
    quantity: Optional[int] = None
    bid_type: Optional[int] = None
    status: Optional[int] = None
    is_high_value: bool = False
    ministry_name: Optional[str] = None
    dept_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    consignee_state: Optional[str] = None
    consignee_city: Optional[str] = None
    bid_url: Optional[str] = None
    cat_id: Optional[str] = None


class BidCreate(BidBase):
    pass


class BidOut(BidBase):
    id: int
    first_seen_at: datetime

    model_config = {"from_attributes": True}


# ─── PROFILE SCHEMAS ─────────────────────────────────────────────────────────

class ProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    is_active: bool = True
    state: str = Field(..., min_length=1)
    cities: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    ministry_filter: Optional[List[str]] = None
    poll_interval_seconds: int = 300


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    cities: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
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
    notification_sent: bool
    notification_sent_at: Optional[datetime] = None
    notification_error: Optional[str] = None
    retry_count: int
    created_at: datetime
    bid: Optional[BidOut] = None

    model_config = {"from_attributes": True}


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
    total_alerts: int
    last_check: Optional[datetime]
