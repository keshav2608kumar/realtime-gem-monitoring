"""
Alerts Router — Verified alert history, acknowledgement management & accurate database counters
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timezone

from app.database import get_db
from app.models import Alert, Bid
from app.schemas import AlertOut, AlertCountStats
from app.routers.bids import _enrich_bid
from app.services.datetime_service import UTC_TZ

router = APIRouter(prefix="/alerts", tags=["Alerts"])


def _enrich_alert(a: Alert) -> AlertOut:
    """Enrich Alert with formatted BidOut details."""
    enriched_bid = _enrich_bid(a.bid) if a.bid else None
    return AlertOut(
        id=a.id,
        profile_id=a.profile_id,
        bid_id=a.bid_id,
        matched_keywords=a.matched_keywords,
        match_reason=a.match_reason or (f"Matched profile #{a.profile_id}" if a.matched_keywords else "Filter match"),
        status=a.status or ("ACKNOWLEDGED" if a.acknowledged else "NEW"),
        acknowledged=bool(a.acknowledged),
        acknowledged_at=a.acknowledged_at,
        notification_sent=bool(a.notification_sent),
        notification_sent_at=a.notification_sent_at,
        notification_error=a.notification_error,
        retry_count=a.retry_count or 0,
        created_at=a.created_at or datetime.now(UTC_TZ),
        bid=enriched_bid,
    )


@router.get("/", response_model=List[AlertOut])
def list_alerts(
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    unacknowledged_only: bool = False,
    profile_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    List alerts ordered by creation time (most recent first).
    Every alert card references the exact normalized bid record.
    """
    q = db.query(Alert).options(joinedload(Alert.bid)).order_by(desc(Alert.created_at))
    if unacknowledged_only:
        q = q.filter(Alert.acknowledged == False)
    if profile_id:
        q = q.filter(Alert.profile_id == profile_id)
    raw_alerts = q.offset(skip).limit(limit).all()
    return [_enrich_alert(a) for a in raw_alerts]


@router.get("/stats", response_model=AlertCountStats)
def get_alert_stats(db: Session = Depends(get_db)):
    """
    Returns exact persisted database counters for fired alerts.
    Does NOT calculate counts from a temporary frontend array.
    """
    total = db.query(Alert).count()
    new_count = db.query(Alert).filter(Alert.status == "NEW").count()
    unack = db.query(Alert).filter(Alert.acknowledged == False).count()
    ack = db.query(Alert).filter(Alert.acknowledged == True).count()
    dispatched = db.query(Alert).filter(Alert.notification_sent == True).count()
    failed = db.query(Alert).filter(Alert.notification_error != None).count()

    return AlertCountStats(
        total_alerts=total,
        new_alerts=new_count,
        unacknowledged_alerts=unack,
        acknowledged_alerts=ack,
        dispatched_notifications=dispatched,
        failed_notifications=failed,
    )


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    a = db.query(Alert).options(joinedload(Alert.bid)).filter(Alert.id == alert_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    return _enrich_alert(a)


@router.post("/{alert_id}/ack")
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Mark an alert as acknowledged by user."""
    a = db.query(Alert).filter(Alert.id == alert_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    a.acknowledged = True
    a.acknowledged_at = datetime.now(UTC_TZ)
    a.status = "ACKNOWLEDGED"
    db.commit()
    return {"status": "success", "alert_id": alert_id, "acknowledged": True}


@router.post("/ack-all")
def acknowledge_all_alerts(db: Session = Depends(get_db)):
    """Acknowledge all pending unacknowledged alerts."""
    now = datetime.now(UTC_TZ)
    updated = db.query(Alert).filter(Alert.acknowledged == False).update({
        "acknowledged": True,
        "acknowledged_at": now,
        "status": "ACKNOWLEDGED",
    })
    db.commit()
    return {"status": "success", "acknowledged_count": updated}


@router.post("/{alert_id}/retry-notify")
def retry_notification(alert_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Manually trigger notification for an alert."""
    from app.notifications.fcm_sender import send_alert_notifications
    a = db.query(Alert).filter(Alert.id == alert_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    background_tasks.add_task(send_alert_notifications, alert_id)
    return {"message": "Notification retry queued"}
