"""
Health Router — System status, monitor health, manual poll trigger
"""
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_
from typing import List
from datetime import datetime, timezone

from app.database import get_db
from app.models import Profile, Bid, Alert, MonitorHealth
from app.schemas import HealthOut, SystemStatus
from app.workers.scheduler import get_scheduler_status
from app.services.datetime_service import UTC_TZ

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/", response_model=SystemStatus)
def get_system_status(db: Session = Depends(get_db)):
    now = datetime.now(UTC_TZ)
    total_profiles = db.query(Profile).count()
    active_profiles = db.query(Profile).filter(Profile.is_active == True).count()
    total_bids = db.query(Bid).count()
    active_bids = db.query(Bid).filter(or_(Bid.end_date == None, Bid.end_date > now)).count()
    expired_bids = db.query(Bid).filter(and_(Bid.end_date != None, Bid.end_date <= now)).count()
    total_alerts = db.query(Alert).count()
    unack_alerts = db.query(Alert).filter(Alert.acknowledged == False).count()

    last_health = db.query(MonitorHealth).order_by(desc(MonitorHealth.checked_at)).first()
    scheduler = get_scheduler_status()

    return SystemStatus(
        status="ok",
        monitor_running=scheduler["running"],
        total_profiles=total_profiles,
        active_profiles=active_profiles,
        total_bids_in_db=total_bids,
        active_bids_in_db=active_bids,
        expired_bids_in_db=expired_bids,
        total_alerts=total_alerts,
        unacknowledged_alerts=unack_alerts,
        last_check=last_health.checked_at if last_health else None,
    )


@router.get("/history", response_model=List[HealthOut])
def get_health_history(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(MonitorHealth)
        .order_by(desc(MonitorHealth.checked_at))
        .offset(skip).limit(limit).all()
    )


@router.post("/trigger-poll")
def trigger_manual_poll(background_tasks: BackgroundTasks):
    """Manually trigger a poll of all active profiles immediately."""
    from app.workers.monitor_worker import poll_all_active_profiles
    background_tasks.add_task(poll_all_active_profiles)
    return {"message": "Manual poll triggered in background"}


@router.get("/debug-gem")
def debug_gem_connection():
    """Diagnose direct connectivity from this cloud server to GeM portal."""
    import traceback
    from app.gem import GemSession, GemFetcher

    results = {}
    try:
        session = GemSession()
        session.refresh()
        results["csrf_obtained"] = bool(session._csrf_token)
        results["csrf_preview"] = session._csrf_token[:8] if session._csrf_token else None
    except Exception as e:
        results["session_refresh_error"] = str(e)
        results["session_refresh_trace"] = traceback.format_exc()
        return results

    try:
        fetcher = GemFetcher(session)
        bids, total = fetcher.fetch_bids_by_location(state="KARNATAKA", city="BANGALORE", page=1)
        results["search_bids_total"] = total
        results["search_bids_page1_count"] = len(bids)
        if bids:
            results["sample_bid_number"] = bids[0].get("b_bid_number")
            results["sample_category"] = bids[0].get("b_category_name")
    except Exception as e:
        results["search_bids_error"] = str(e)
        results["search_bids_trace"] = traceback.format_exc()

    return results
